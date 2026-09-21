<?php

declare(strict_types=1);

namespace Capcov\PHPStan;

use PhpParser\Node;
use PHPStan\Analyser\Scope;
use PHPStan\Node\FileNode;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;
use PHPStan\Type\MixedType;
use PHPStan\Type\ObjectType;
use PHPStan\Type\Type;

/**
 * capcov's incumbent edge producer: PHPStan says what a receiver IS, these rules
 * write down what that makes the call, and every site it cannot type is named.
 *
 * Each rule emits one non-ignorable message per fact, spelled
 *
 *     capcov-fact:{"fact": "...", ...}
 *
 * so the facts travel in PHPStan's own `--error-format=json` document and need
 * no second output channel. `capcov.claims.static.phpstan_facts` reads those
 * messages, ignores every other message in the report (a real analysis has real
 * errors in it, and they are not facts about the call graph) and turns them into
 * the static claim schema.
 *
 * Two disciplines matter more than coverage:
 *
 * 1. A site whose receiver is `mixed`, or whose method is magic (`__call`), is
 *    emitted as an `unresolved` fact with the reason, NEVER dropped and never
 *    guessed. PHPStan's own "call on mixed" is the residue, and it names the
 *    line. The Python side turns those into `static_unresolved_call_site`, and
 *    `call_graph_closed` is withheld for any scope that carries one.
 * 2. Every resolved edge carries the KIND of resolution that produced it --
 *    `direct` (a declared method on a known class), `larastan-facade`,
 *    `larastan-model-forward`, `larastan-container`, `direct-propel` -- so a
 *    reader can tell a typed call from a framework assumption without rerunning
 *    anything. Facade and container resolutions are assumptions about framework
 *    behaviour; they are labelled as such and classed `phpstan`, never `scip`.
 *
 * Paths are reported relative to the analysed root (`%currentWorkingDirectory%`,
 * passed in by `phpstan-capcov.neon`) so a report is the same document whichever
 * machine produced it.
 */
abstract class CapcovFactRule implements Rule
{
    /** @var string */
    protected $root;

    public function __construct(string $root)
    {
        $this->root = rtrim($root, '/') . '/';
    }

    /** @param array<string, mixed> $payload */
    protected function fact(array $payload): \PHPStan\Rules\RuleError
    {
        return RuleErrorBuilder::message('capcov-fact:' . json_encode($payload, JSON_UNESCAPED_SLASHES))
            ->identifier('capcov.fact')
            ->nonIgnorable()
            ->build();
    }

    protected function relative(string $file): string
    {
        return strpos($file, $this->root) === 0 ? substr($file, strlen($this->root)) : $file;
    }

    /** The innermost function or method the node sits in, or null at module scope. */
    protected function caller(Scope $scope): ?string
    {
        $function = $scope->getFunction();
        if ($function === null) {
            return null;
        }
        $class = $scope->getClassReflection();

        return $class === null
            ? $function->getName()
            : $class->getName() . '::' . $function->getName();
    }
}

/** One `analysed` fact per file: the census is the analysis, and this is its extent. */
final class CapcovFileCollector extends CapcovFactRule
{
    public function getNodeType(): string
    {
        return FileNode::class;
    }

    public function processNode(Node $node, Scope $scope): array
    {
        return [$this->fact(['fact' => 'analysed', 'path' => $this->relative($scope->getFile())])];
    }
}

/** Class declarations: the symbol, and the entity when it names its table literally. */
final class CapcovClassCollector extends CapcovFactRule
{
    public function getNodeType(): string
    {
        return Node\Stmt\Class_::class;
    }

    public function processNode(Node $node, Scope $scope): array
    {
        if ($node->namespacedName === null) {
            return [];
        }
        $name = $node->namespacedName->toString();
        $path = $this->relative($scope->getFile());
        $facts = [$this->fact([
            'fact' => 'symbol', 'symbol' => $name, 'kind' => 'class', 'category' => 'type',
            'display' => $node->name === null ? $name : $node->name->toString(),
            'path' => $path, 'line' => $node->getStartLine(),
        ])];
        foreach ($node->getProperties() as $property) {
            foreach ($property->props as $item) {
                if ($item->name->toString() !== 'table' || !$item->default instanceof Node\Scalar\String_) {
                    continue;
                }
                $facts[] = $this->fact([
                    'fact' => 'entity', 'entity' => $name, 'table' => $item->default->value,
                    'path' => $path, 'line' => $property->getStartLine(),
                ]);
            }
        }

        return $facts;
    }
}

/** Method declarations: the callable symbols routes and edges are attributed to. */
final class CapcovMethodCollector extends CapcovFactRule
{
    public function getNodeType(): string
    {
        return Node\Stmt\ClassMethod::class;
    }

    public function processNode(Node $node, Scope $scope): array
    {
        $class = $scope->getClassReflection();
        if ($class === null) {
            return [];
        }
        $symbol = $class->getName() . '::' . $node->name->toString();

        return [$this->fact([
            'fact' => 'symbol', 'symbol' => $symbol, 'kind' => 'method', 'category' => 'callable',
            'display' => $node->name->toString(),
            'path' => $this->relative($scope->getFile()), 'line' => $node->getStartLine(),
        ])];
    }
}

/**
 * Calls: one resolved edge with its resolution kind, or one named unresolved site.
 *
 * The facade and container tables come from `phpstan-capcov.neon` so a project
 * can name its own without editing this file; the storage verbs are the sink
 * table `static_op_site` is written from.
 */
final class CapcovCallCollector extends CapcovFactRule
{
    private const VERBS = [
        'find' => 'read', 'get' => 'read', 'first' => 'read', 'pluck' => 'read',
        'all' => 'read', 'doSelect' => 'read',
        'create' => 'create', 'insert' => 'create', 'doInsert' => 'create',
        'save' => 'update', 'update' => 'update', 'doUpdate' => 'update',
        'delete' => 'delete', 'destroy' => 'delete', 'doDelete' => 'delete',
    ];
    private const CONTAINER_FUNCTIONS = ['app', 'resolve'];

    /** @var array<string, string> facade class => the accessor class it resolves to */
    private $facades;
    /** @var array<string, string> model base class => the builder statics forward to */
    private $models;
    /** @var list<string> route registrars, whose calls CapcovRouteCollector owns */
    private $routes;

    /**
     * @param array<string, string> $facades
     * @param array<string, string> $models
     * @param list<string> $routes
     */
    public function __construct(string $root, array $facades, array $models, array $routes)
    {
        parent::__construct($root);
        $this->facades = $facades;
        $this->models = $models;
        $this->routes = $routes;
    }

    public function getNodeType(): string
    {
        return Node\Expr\CallLike::class;
    }

    public function processNode(Node $node, Scope $scope): array
    {
        $path = $this->relative($scope->getFile());
        $line = $node->getStartLine();
        $caller = $this->caller($scope);
        if ($node instanceof Node\Expr\StaticCall) {
            return $this->staticCall($node, $scope, $path, $line, $caller);
        }
        if ($node instanceof Node\Expr\MethodCall || $node instanceof Node\Expr\NullsafeMethodCall) {
            return $this->methodCall($node, $scope, $path, $line, $caller);
        }
        if ($node instanceof Node\Expr\New_) {
            return $node->class instanceof Node\Name
                ? $this->edge($caller, $scope->resolveName($node->class) . '::__construct', 'direct', $path, $line)
                : [$this->unresolved($this->shape($node), 'dynamic-method', $path, $line, $caller)];
        }
        if ($node instanceof Node\Expr\FuncCall) {
            return $node->name instanceof Node\Name
                ? $this->funcCall($node, $scope, $path, $line, $caller)
                : [$this->unresolved($this->shape($node), 'dynamic-method', $path, $line, $caller)];
        }

        return [$this->unresolved($this->shape($node), 'dynamic-method', $path, $line, $caller)];
    }

    /** @return list<\PHPStan\Rules\RuleError> */
    private function staticCall(Node\Expr\StaticCall $node, Scope $scope, string $path, int $line, ?string $caller): array
    {
        if (!$node->class instanceof Node\Name || !$node->name instanceof Node\Identifier) {
            return [$this->unresolved($this->shape($node), 'dynamic-method', $path, $line, $caller)];
        }
        $class = $scope->resolveName($node->class);
        if (in_array($class, $this->routes, true)) {
            return [];  // CapcovRouteCollector owns route registrations.
        }
        $method = $node->name->toString();
        if (isset($this->facades[$class])) {
            // Larastan resolves a facade to its accessor; the edge is an
            // assumption about the framework and says so in its kind.
            $table = $this->literalTable($node);
            $facts = $this->edge($caller, $this->facades[$class] . '::' . $method, 'larastan-facade',
                $path, $line, $this->operation($method, $table, true, $path, $line, $caller));
            if ($table !== null) {
                // `DB::table('x')` is the only place a query-builder chain names
                // its store, so the entity is declared here rather than in a
                // class: without it the op site below binds to nothing.
                $facts[] = $this->fact([
                    'fact' => 'entity', 'entity' => $table, 'table' => $table,
                    'path' => $path, 'line' => $line,
                ]);
            }

            return $facts;
        }
        $declaring = $this->declaringClass($scope, $class, $method);
        $storage = $this->isStorageClass($class);
        if ($declaring !== null) {
            $kind = $this->isPropelPeer($class) ? 'direct-propel' : 'direct';

            return $this->edge($caller, $declaring . '::' . $method, $kind, $path, $line,
                $this->operation($method, $class, $storage, $path, $line, $caller));
        }
        $builder = $this->modelBuilder($class);
        if ($builder !== null) {
            // An Eloquent static nothing declares forwards to the query builder.
            return $this->edge($caller, $builder . '::' . $method, 'larastan-model-forward', $path, $line,
                $this->operation($method, $class, $storage, $path, $line, $caller));
        }

        return [$this->unresolved($class . '::' . $method, 'magic-call', $path, $line, $caller)];
    }

    /** @return list<\PHPStan\Rules\RuleError> */
    private function methodCall(Node\Expr $node, Scope $scope, string $path, int $line, ?string $caller): array
    {
        if (!$node->name instanceof Node\Identifier) {
            return [$this->unresolved($this->shape($node), 'dynamic-method', $path, $line, $caller)];
        }
        $method = $node->name->toString();
        $accessor = $this->facadeAccessor($node->var, $scope);
        if ($accessor !== null) {
            // `DB::table('x')->insert(...)`: the receiver is the facade's
            // accessor by the same assumption the static call was resolved by,
            // and the table is the literal the source names.
            return $this->edge($caller, $accessor . '::' . $method, 'larastan-facade', $path, $line,
                $this->operation($method, $this->literalTable($node->var), true, $path, $line, $caller));
        }
        $type = $scope->getType($node->var);
        if ($type instanceof MixedType) {
            return [$this->unresolved('->' . $method, 'mixed-receiver', $path, $line, $caller)];
        }
        $classes = $this->classNames($type);
        if ($classes === []) {
            return [$this->unresolved('->' . $method, 'mixed-receiver', $path, $line, $caller)];
        }
        $facts = [];
        foreach ($classes as $class) {
            $declaring = $this->declaringClass($scope, $class, $method);
            if ($declaring === null) {
                $facts[] = $this->unresolved($class . '->' . $method, 'magic-call', $path, $line, $caller);
                continue;
            }
            $facts = array_merge($facts, $this->edge($caller, $declaring . '::' . $method, 'direct', $path, $line,
                $this->operation($method, $class, $this->isStorageClass($class), $path, $line, $caller)));
        }

        return $facts;
    }

    /** @return list<\PHPStan\Rules\RuleError> */
    private function funcCall(Node\Expr\FuncCall $node, Scope $scope, string $path, int $line, ?string $caller): array
    {
        $name = $node->name->toString();
        if (!in_array($name, self::CONTAINER_FUNCTIONS, true)) {
            return $this->edge($caller, $name, 'direct', $path, $line);
        }
        $argument = $node->getArgs()[0] ?? null;
        if ($argument !== null && $argument->value instanceof Node\Expr\ClassConstFetch
            && $argument->value->class instanceof Node\Name) {
            // `app(X::class)` / `resolve(X::class)`: the container binding is a
            // class literal, which is the one container shape that is readable.
            return $this->edge($caller, $scope->resolveName($argument->value->class) . '::__construct',
                'larastan-container', $path, $line);
        }

        return [$this->unresolved($name . '()', 'dynamic-method', $path, $line, $caller)];
    }

    /**
     * @param \PHPStan\Rules\RuleError|null $operation
     * @return list<\PHPStan\Rules\RuleError>
     */
    private function edge(?string $caller, string $callee, string $kind, string $path, int $line, $operation = null): array
    {
        if ($caller === null) {
            // No enclosing function: there is nothing to attribute the edge to,
            // so the site is enumerated instead of attributed to the file.
            return [$this->unresolved($callee, 'caller-unattributed', $path, $line, null)];
        }
        $facts = [$this->fact([
            'fact' => 'call', 'caller' => $caller, 'callee' => $callee, 'kind' => $kind,
            'path' => $path, 'line' => $line,
        ])];
        if ($operation !== null) {
            $facts[] = $operation;
        }

        return $facts;
    }

    private function unresolved(string $callee, string $reason, string $path, int $line, ?string $caller): \PHPStan\Rules\RuleError
    {
        $payload = ['fact' => 'unresolved', 'callee' => $callee, 'reason' => $reason,
                    'path' => $path, 'line' => $line];
        if ($caller !== null) {
            $payload['caller'] = $caller;
        }

        return $this->fact($payload);
    }

    /**
     * The storage operation this call is, or null when it is not one.
     *
     * `$storage` is whether the RECEIVER is a store at all -- a model, a Propel
     * peer, a facade's query builder. Without it every `$repository->get()`
     * would become a read of the repository class, and `static_capability_op`
     * would name classes that are not entities.
     */
    private function operation(string $method, ?string $entity, bool $storage, string $path, int $line, ?string $caller): ?\PHPStan\Rules\RuleError
    {
        if (!isset(self::VERBS[$method]) || !$storage || $caller === null) {
            return null;
        }
        if ($entity === null) {
            // A store whose table the source does not name: enumerated, never
            // guessed, and the reason is the shape that defeated it.
            return $this->unresolved($method, 'non-literal-entity', $path, $line, $caller);
        }

        return $this->fact([
            'fact' => 'op', 'verb' => self::VERBS[$method], 'entity' => $entity,
            'path' => $path, 'line' => $line, 'caller' => $caller,
        ]);
    }

    /** The accessor class a facade receiver resolves to, by the neon's table. */
    private function facadeAccessor(Node\Expr $receiver, Scope $scope): ?string
    {
        if (!$receiver instanceof Node\Expr\StaticCall || !$receiver->class instanceof Node\Name) {
            return null;
        }
        $class = $scope->resolveName($receiver->class);

        return $this->facades[$class] ?? null;
    }

    /** The table a call names literally: `DB::table('x')` is that one shape. */
    private function literalTable(Node\Expr $call): ?string
    {
        if (!$call instanceof Node\Expr\StaticCall) {
            return null;
        }
        $argument = $call->getArgs()[0] ?? null;

        return $argument !== null && $argument->value instanceof Node\Scalar\String_
            ? $argument->value->value
            : null;
    }

    private function isStorageClass(string $class): bool
    {
        return $this->modelBuilder($class) !== null || $this->isPropelPeer($class);
    }

    private function declaringClass(Scope $scope, string $class, string $method): ?string
    {
        $objectType = new ObjectType($class);
        if (!$objectType->hasMethod($method)->yes()) {
            return null;
        }

        return $objectType->getMethod($method, $scope)->getDeclaringClass()->getName();
    }

    /** The builder an Eloquent static forwards to, when the class is a model. */
    private function modelBuilder(string $class): ?string
    {
        foreach ($this->models as $base => $builder) {
            if ((new ObjectType($base))->isSuperTypeOf(new ObjectType($class))->yes()) {
                return $builder;
            }
        }

        return null;
    }

    private function isPropelPeer(string $class): bool
    {
        return substr($class, -4) === 'Peer' || substr($class, -5) === 'Query';
    }

    /** @return list<string> */
    private function classNames(Type $type): array
    {
        return array_values(array_filter($type->getObjectClassNames(), 'is_string'));
    }

    /** What the source spells at a site nothing can be resolved from. */
    private function shape(Node $node): string
    {
        $class = get_class($node);
        $short = strrchr($class, '\\');

        return $short === false ? $class : substr($short, 1);
    }
}

/**
 * Route registrations, literal only: `Route::get('/x', [Ctl::class, 'm'])`.
 *
 * A closure handler, a `Route::resource`, a variable path -- anything whose
 * surface or handler is not in the source as a literal -- is emitted as
 * `route_excluded` with the reason, and the Python side withholds
 * `static_route_inventory_closed` while any such row exists. Running the
 * framework's own router (`php artisan route:list`) would resolve them and is
 * a framework assumption, not a fact about the source; it belongs in an
 * assumption row, not here.
 */
final class CapcovRouteCollector extends CapcovFactRule
{
    private const VERBS = ['get' => 'GET', 'post' => 'POST', 'put' => 'PUT',
                           'patch' => 'PATCH', 'delete' => 'DELETE', 'options' => 'OPTIONS'];
    private const NON_LITERAL = ['resource', 'apiResource', 'match', 'any', 'group', 'redirect'];

    /** @var list<string> the route facade classes */
    private $routes;

    /** @param list<string> $routes */
    public function __construct(string $root, array $routes)
    {
        parent::__construct($root);
        $this->routes = $routes;
    }

    public function getNodeType(): string
    {
        return Node\Expr\StaticCall::class;
    }

    public function processNode(Node $node, Scope $scope): array
    {
        if (!$node->class instanceof Node\Name || !$node->name instanceof Node\Identifier) {
            return [];
        }
        if (!in_array($scope->resolveName($node->class), $this->routes, true)) {
            return [];
        }
        $method = $node->name->toString();
        $path = $this->relative($scope->getFile());
        $line = $node->getStartLine();
        $arguments = $node->getArgs();
        $uri = ($arguments[0] ?? null) !== null && $arguments[0]->value instanceof Node\Scalar\String_
            ? $arguments[0]->value->value
            : null;
        if (!isset(self::VERBS[$method]) || $uri === null) {
            return [$this->fact([
                'fact' => 'route_excluded',
                'surface' => 'php:Route::' . $method . ($uri === null ? '' : ' ' . $uri),
                'reason' => in_array($method, self::NON_LITERAL, true) ? 'non-literal-route' : 'unknown-verb',
                'path' => $path, 'line' => $line,
            ])];
        }
        $surface = 'http:' . self::VERBS[$method] . ' ' . $uri;
        $handler = $arguments[1] ?? null;
        $value = $handler === null ? null : $handler->value;
        if ($value instanceof Node\Expr\Array_ && count($value->items) === 2
            && $value->items[0] !== null && $value->items[1] !== null
            && $value->items[0]->value instanceof Node\Expr\ClassConstFetch
            && $value->items[0]->value->class instanceof Node\Name
            && $value->items[1]->value instanceof Node\Scalar\String_) {
            $class = $scope->resolveName($value->items[0]->value->class);

            return [$this->fact([
                'fact' => 'route', 'surface' => $surface,
                'handler' => $class . '::' . $value->items[1]->value->value,
                'path' => $path, 'line' => $line,
            ])];
        }

        return [$this->fact([
            'fact' => 'route_excluded', 'surface' => $surface,
            'reason' => 'non-literal-handler', 'path' => $path, 'line' => $line,
        ])];
    }
}
