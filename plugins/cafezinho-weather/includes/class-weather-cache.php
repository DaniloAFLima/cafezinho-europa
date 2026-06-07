<?php
/**
 * Gerencia o transient `cafezinho_weather` com merge gracioso por cidade.
 */

if ( ! defined( 'HOUR_IN_SECONDS_FALLBACK' ) ) {
    // WP defines HOUR_IN_SECONDS = 3600; tests run without WP loaded, so we
    // provide a constant the class uses regardless of environment.
    define( 'HOUR_IN_SECONDS_FALLBACK', defined( 'HOUR_IN_SECONDS' ) ? HOUR_IN_SECONDS : 3600 );
}

class Cafezinho_Weather_Cache {

    public const TRANSIENT_KEY = 'cafezinho_weather';
    public const TTL_SECONDS   = 3 * HOUR_IN_SECONDS_FALLBACK;

    public static function get(): ?array {
        $v = get_transient( self::TRANSIENT_KEY );
        return ( is_array( $v ) && isset( $v['cities'] ) ) ? $v : null;
    }

    /**
     * Mescla `$fresh` com o cache existente. Cidades ausentes em `$fresh` mantêm
     * a leitura anterior.
     */
    public static function merge_and_store( array $fresh ): void {
        $existing = self::get() ?? [ 'cities' => [] ];
        $merged   = $existing['cities'];

        foreach ( $fresh as $slug => $city ) {
            $merged[ $slug ] = $city;
        }

        // If nothing fresh AND nothing existing, don't write garbage.
        if ( empty( $merged ) ) {
            return;
        }

        $payload = [
            'updated_at' => time(),
            'cities'     => $merged,
        ];
        set_transient( self::TRANSIENT_KEY, $payload, self::TTL_SECONDS );
    }

    public static function clear(): void {
        delete_transient( self::TRANSIENT_KEY );
    }
}
