<?php
/**
 * Cliente Open-Meteo para o widget de previsão.
 */
class Cafezinho_Weather_Fetcher {

    private const ENDPOINT = 'https://api.open-meteo.com/v1/forecast';
    private const TIMEOUT  = 5;
    private const DAYS     = 3;

    /**
     * Valida e normaliza a resposta crua da Open-Meteo.
     *
     * @return array<int, array{date:string,max:int,min:int,code:int}>
     * @throws RuntimeException se a resposta estiver malformada.
     */
    public static function parse_response( array $raw ): array {
        if ( ! isset( $raw['daily'] ) || ! is_array( $raw['daily'] ) ) {
            throw new RuntimeException( 'Open-Meteo response missing "daily" key' );
        }
        $d = $raw['daily'];
        foreach ( [ 'time', 'temperature_2m_max', 'temperature_2m_min', 'weather_code' ] as $k ) {
            if ( ! isset( $d[ $k ] ) || ! is_array( $d[ $k ] ) ) {
                throw new RuntimeException( "Open-Meteo response missing array key: $k" );
            }
        }
        $n = count( $d['time'] );
        if ( $n < self::DAYS ) {
            throw new RuntimeException( "Open-Meteo response has only $n days; expected " . self::DAYS );
        }
        foreach ( [ 'temperature_2m_max', 'temperature_2m_min', 'weather_code' ] as $k ) {
            if ( count( $d[ $k ] ) !== $n ) {
                throw new RuntimeException( "Open-Meteo response array length mismatch on: $k" );
            }
        }

        $days = [];
        for ( $i = 0; $i < self::DAYS; $i++ ) {
            if ( ! is_numeric( $d['temperature_2m_max'][ $i ] ) ||
                 ! is_numeric( $d['temperature_2m_min'][ $i ] ) ||
                 ! is_numeric( $d['weather_code'][ $i ] ) ) {
                throw new RuntimeException( "Open-Meteo response non-numeric value at index $i" );
            }
            $days[] = [
                'date' => (string) $d['time'][ $i ],
                'max'  => (int) round( $d['temperature_2m_max'][ $i ] ),
                'min'  => (int) round( $d['temperature_2m_min'][ $i ] ),
                'code' => (int) $d['weather_code'][ $i ],
            ];
        }
        return $days;
    }

    public static function build_url( float $lat, float $lon ): string {
        return self::ENDPOINT . '?' . http_build_query( [
            'latitude'      => $lat,
            'longitude'     => $lon,
            'daily'         => 'temperature_2m_max,temperature_2m_min,weather_code',
            'timezone'      => 'auto',
            'forecast_days' => self::DAYS,
        ] );
    }

    /**
     * Busca dados de todas as cidades em paralelo.
     * Cidades que falharem ficam ausentes do array devolvido (merge cuida do fallback).
     *
     * @param array<string, array{country:string,city:string,flag:string,lat:float,lon:float}> $cities
     * @return array<string, array{country:string,city:string,flag:string,fetched_at:int,days:array}>
     */
    public static function fetch_all( array $cities ): array {
        if ( ! class_exists( 'WpOrg\\Requests\\Requests' ) && ! class_exists( 'Requests' ) ) {
            throw new RuntimeException( 'WordPress Requests library not available' );
        }
        $requests_class = class_exists( 'WpOrg\\Requests\\Requests' ) ? 'WpOrg\\Requests\\Requests' : 'Requests';

        $requests = [];
        foreach ( $cities as $slug => $cfg ) {
            $requests[ $slug ] = [
                'url'     => self::build_url( $cfg['lat'], $cfg['lon'] ),
                'type'    => $requests_class::GET,
                'options' => [ 'timeout' => self::TIMEOUT ],
            ];
        }

        $responses = $requests_class::request_multiple( $requests );
        $now       = time();
        $out       = [];

        foreach ( $responses as $slug => $resp ) {
            $cfg = $cities[ $slug ];
            try {
                if ( $resp instanceof \Exception || $resp instanceof \Throwable ) {
                    throw new RuntimeException( 'HTTP error: ' . $resp->getMessage() );
                }
                if ( $resp->status_code !== 200 ) {
                    throw new RuntimeException( "HTTP {$resp->status_code} for {$cfg['city']}" );
                }
                $raw  = json_decode( $resp->body, true );
                if ( ! is_array( $raw ) ) {
                    throw new RuntimeException( "Invalid JSON for {$cfg['city']}" );
                }
                $days = self::parse_response( $raw );
                $out[ $slug ] = [
                    'country'    => $cfg['country'],
                    'city'       => $cfg['city'],
                    'flag'       => $cfg['flag'],
                    'fetched_at' => $now,
                    'days'       => $days,
                ];
            } catch ( Throwable $e ) {
                error_log( '[cafezinho-weather] fetch failed for ' . $slug . ': ' . $e->getMessage() );
            }
        }
        return $out;
    }
}
