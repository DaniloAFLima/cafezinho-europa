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
}
