<?php
use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../includes/class-weather-cache.php';

class WeatherCacheTest extends TestCase {

    protected function setUp(): void {
        $GLOBALS['__cw_transients'] = [];
    }

    private function city( string $slug, int $max ): array {
        return [
            'country'    => 'X',
            'city'       => ucfirst( $slug ),
            'flag'       => 'xx',
            'fetched_at' => 1000,
            'days'       => [
                [ 'date' => '2026-06-07', 'max' => $max, 'min' => 10, 'code' => 3 ],
                [ 'date' => '2026-06-08', 'max' => $max, 'min' => 10, 'code' => 3 ],
                [ 'date' => '2026-06-09', 'max' => $max, 'min' => 10, 'code' => 3 ],
            ],
        ];
    }

    public function test_get_returns_null_when_empty() {
        $this->assertNull( Cafezinho_Weather_Cache::get() );
    }

    public function test_merge_and_store_full_fresh_data() {
        $fresh = [
            'paris'    => $this->city( 'paris', 18 ),
            'londres'  => $this->city( 'londres', 14 ),
        ];
        Cafezinho_Weather_Cache::merge_and_store( $fresh );
        $cached = Cafezinho_Weather_Cache::get();
        $this->assertCount( 2, $cached['cities'] );
        $this->assertSame( 18, $cached['cities']['paris']['days'][0]['max'] );
        $this->assertArrayHasKey( 'updated_at', $cached );
    }

    public function test_merge_preserves_missing_city_from_previous_cache() {
        Cafezinho_Weather_Cache::merge_and_store( [
            'paris'   => $this->city( 'paris', 18 ),
            'londres' => $this->city( 'londres', 14 ),
        ] );
        // Second refresh: only paris came back; londres failed.
        Cafezinho_Weather_Cache::merge_and_store( [
            'paris' => $this->city( 'paris', 20 ),
        ] );
        $cached = Cafezinho_Weather_Cache::get();
        $this->assertSame( 20, $cached['cities']['paris']['days'][0]['max'] );
        $this->assertSame( 14, $cached['cities']['londres']['days'][0]['max'], 'londres should keep old reading' );
    }

    public function test_merge_with_empty_fresh_does_not_wipe_cache() {
        Cafezinho_Weather_Cache::merge_and_store( [
            'paris' => $this->city( 'paris', 18 ),
        ] );
        Cafezinho_Weather_Cache::merge_and_store( [] );
        $cached = Cafezinho_Weather_Cache::get();
        $this->assertSame( 18, $cached['cities']['paris']['days'][0]['max'] );
    }

    public function test_clear_removes_cache() {
        Cafezinho_Weather_Cache::merge_and_store( [
            'paris' => $this->city( 'paris', 18 ),
        ] );
        Cafezinho_Weather_Cache::clear();
        $this->assertNull( Cafezinho_Weather_Cache::get() );
    }
}
