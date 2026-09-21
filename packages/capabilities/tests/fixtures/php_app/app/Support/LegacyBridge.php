<?php

namespace App\Support;

class LegacyBridge
{
    public function __call($name, $arguments)
    {
        return null;
    }
}
