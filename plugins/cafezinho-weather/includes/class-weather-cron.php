<?php
/**
 * Registra evento WP-Cron a cada 2h e dispara o refresh.
 */
class Cafezinho_Weather_Cron {

    public const HOOK          = 'cafezinho_weather_refresh';
    public const SCHEDULE      = 'cafezinho_2h';
    public const LOCK_KEY      = 'cafezinho_weather_lock';
    public const LOCK_TTL      = 60;
    public const FAILURE_KEY   = 'cafezinho_weather_consecutive_failures';

    public static function register_schedule( array $schedules ): array {
        $schedules[ self::SCHEDULE ] = [
            'interval' => 2 * HOUR_IN_SECONDS,
            'display'  => 'A cada 2 horas (Cafezinho Weather)',
        ];
        return $schedules;
    }

    public static function on_activate(): void {
        if ( ! wp_next_scheduled( self::HOOK ) ) {
            wp_schedule_event( time() + 30, self::SCHEDULE, self::HOOK );
        }
    }

    public static function on_deactivate(): void {
        wp_clear_scheduled_hook( self::HOOK );
        delete_transient( self::LOCK_KEY );
    }

    /**
     * Handler do hook. Pega o lock, busca os 6 países e mescla.
     */
    public static function handle_refresh(): void {
        if ( get_transient( self::LOCK_KEY ) ) {
            return; // Outra execução em andamento.
        }
        set_transient( self::LOCK_KEY, 1, self::LOCK_TTL );

        try {
            $cities = require CAFEZINHO_WEATHER_PATH . 'config/cities.php';
            $fresh  = Cafezinho_Weather_Fetcher::fetch_all( $cities );
            Cafezinho_Weather_Cache::merge_and_store( $fresh );

            $expected = count( $cities );
            $got      = count( $fresh );
            if ( $got === 0 ) {
                update_option( self::FAILURE_KEY, (int) get_option( self::FAILURE_KEY, 0 ) + 1 );
                error_log( '[cafezinho-weather] refresh: all cities failed' );
            } else {
                update_option( self::FAILURE_KEY, 0 );
                error_log( "[cafezinho-weather] refresh: $got/$expected cities OK" );
            }
        } catch ( Throwable $e ) {
            error_log( '[cafezinho-weather] refresh exception: ' . $e->getMessage() );
        } finally {
            delete_transient( self::LOCK_KEY );
        }
    }
}
