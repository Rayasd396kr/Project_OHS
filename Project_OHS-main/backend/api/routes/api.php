<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Route;

Route::post('/forward-to-lightrag', function (Request $request) {
    $response = Http::timeout(120)->post(
        config('services.ai.url') . '/api/forward-to-lightrag',
        $request->only(['query', 'prompt'])
    );

    return response()->json($response->json(), $response->status());
});

Route::post('/ask/compliance', function (Request $request) {
    $response = Http::timeout(300)->post(
        config('services.ai.url') . '/api/compliance-check',
        $request->only(['query'])
    );

    return response()->json($response->json(), $response->status());
});