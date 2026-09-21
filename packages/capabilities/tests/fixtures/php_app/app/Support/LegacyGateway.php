<?php

namespace App\Support;

use App\Models\Job;

class LegacyGateway
{
    private LegacyBridge $bridge;

    public function __construct(LegacyBridge $bridge)
    {
        $this->bridge = $bridge;
    }

    public function purge(int $id)
    {
        Job::where('id', $id);

        return $this->bridge->purge($id);
    }
}
