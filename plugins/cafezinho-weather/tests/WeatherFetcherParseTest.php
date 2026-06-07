<?php
use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../includes/class-weather-fetcher.php';

class WeatherFetcherParseTest extends TestCase {

    private function load_fixture(): array {
        $raw = file_get_contents( __DIR__ . '/fixtures/open-meteo-paris.json' );
        return json_decode( $raw, true );
    }

    public function test_parse_valid_response_returns_3_days() {
        $days = Cafezinho_Weather_Fetcher::parse_response( $this->load_fixture() );
        $this->assertCount( 3, $days );
    }

    public function test_parse_returns_normalized_keys() {
        $days = Cafezinho_Weather_Fetcher::parse_response( $this->load_fixture() );
        $this->assertArrayHasKey( 'date', $days[0] );
        $this->assertArrayHasKey( 'max',  $days[0] );
        $this->assertArrayHasKey( 'min',  $days[0] );
        $this->assertArrayHasKey( 'code', $days[0] );
    }

    public function test_parse_temperatures_are_rounded_integers() {
        $days = Cafezinho_Weather_Fetcher::parse_response( $this->load_fixture() );
        foreach ( $days as $d ) {
            $this->assertIsInt( $d['max'] );
            $this->assertIsInt( $d['min'] );
            $this->assertIsInt( $d['code'] );
            $this->assertIsString( $d['date'] );
        }
    }

    public function test_parse_throws_on_missing_daily_key() {
        $this->expectException( RuntimeException::class );
        Cafezinho_Weather_Fetcher::parse_response( [ 'foo' => 'bar' ] );
    }

    public function test_parse_throws_on_array_length_mismatch() {
        $bad = [
            'daily' => [
                'time'               => [ '2026-06-07', '2026-06-08' ],
                'temperature_2m_max' => [ 18.0, 19.0, 17.0 ],
                'temperature_2m_min' => [ 11.0, 12.0, 10.0 ],
                'weather_code'       => [ 3, 61, 80 ],
            ],
        ];
        $this->expectException( RuntimeException::class );
        Cafezinho_Weather_Fetcher::parse_response( $bad );
    }

    public function test_parse_throws_on_non_numeric_temperature() {
        $bad = [
            'daily' => [
                'time'               => [ '2026-06-07' ],
                'temperature_2m_max' => [ 'hot' ],
                'temperature_2m_min' => [ 11.0 ],
                'weather_code'       => [ 3 ],
            ],
        ];
        $this->expectException( RuntimeException::class );
        Cafezinho_Weather_Fetcher::parse_response( $bad );
    }
}
