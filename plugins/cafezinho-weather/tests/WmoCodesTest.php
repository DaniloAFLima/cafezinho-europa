<?php
use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../includes/wmo-codes.php';

class WmoCodesTest extends TestCase {

    public function test_sun_code() {
        $r = cafezinho_wmo_lookup( 0 );
        $this->assertSame( 'sun', $r['icon'] );
        $this->assertSame( 'Sol', $r['label'] );
    }

    public function test_partly_cloudy_codes() {
        foreach ( [ 1, 2 ] as $code ) {
            $r = cafezinho_wmo_lookup( $code );
            $this->assertSame( 'sun-cloud', $r['icon'] );
            $this->assertSame( 'Parcialmente nublado', $r['label'] );
        }
    }

    public function test_rain_codes() {
        foreach ( [ 61, 63, 65 ] as $code ) {
            $r = cafezinho_wmo_lookup( $code );
            $this->assertSame( 'rain', $r['icon'] );
            $this->assertSame( 'Chuva', $r['label'] );
        }
    }

    public function test_unknown_code_falls_back() {
        $r = cafezinho_wmo_lookup( 999 );
        $this->assertSame( 'cloud', $r['icon'] );
        $this->assertSame( 'Indefinido', $r['label'] );
    }

    public function test_all_supported_codes_resolve() {
        $codes = [ 0, 1, 2, 3, 45, 48, 51, 53, 55, 61, 63, 65, 71, 73, 75, 80, 81, 82, 95 ];
        foreach ( $codes as $code ) {
            $r = cafezinho_wmo_lookup( $code );
            $this->assertNotSame( 'Indefinido', $r['label'], "Code $code should be mapped" );
        }
    }
}
