<?php
/**
 * Smoke test: chama Open-Meteo de verdade para todas as 6 cidades e
 * valida que `parse_response` aceita cada uma.
 *
 * Uso:  php bin/smoke-weather.php
 * Saída: linha por cidade com hoje/amanhã/depois ou ERRO.
 * Não escreve em cache, não toca em WordPress.
 */

require_once __DIR__ . '/../includes/class-weather-fetcher.php';

$cities  = require __DIR__ . '/../config/cities.php';
$ok      = 0;
$failed  = 0;

foreach ( $cities as $slug => $cfg ) {
    $url = Cafezinho_Weather_Fetcher::build_url( $cfg['lat'], $cfg['lon'] );

    $ctx = stream_context_create( [ 'http' => [ 'timeout' => 5 ] ] );
    $body = @file_get_contents( $url, false, $ctx );
    if ( $body === false ) {
        echo str_pad( $cfg['city'], 12 ) . "  ERRO HTTP\n";
        $failed++;
        continue;
    }
    try {
        $days = Cafezinho_Weather_Fetcher::parse_response( json_decode( $body, true ) );
        printf(
            "%s  hoje %d/%d  amanhã %d/%d  depois %d/%d  (códigos %d/%d/%d)\n",
            str_pad( $cfg['city'], 12 ),
            $days[0]['max'], $days[0]['min'],
            $days[1]['max'], $days[1]['min'],
            $days[2]['max'], $days[2]['min'],
            $days[0]['code'], $days[1]['code'], $days[2]['code']
        );
        $ok++;
    } catch ( Throwable $e ) {
        echo str_pad( $cfg['city'], 12 ) . "  ERRO parse: " . $e->getMessage() . "\n";
        $failed++;
    }
}

echo "\nResumo: $ok ok, $failed falhas\n";
exit( $failed === 0 ? 0 : 1 );
