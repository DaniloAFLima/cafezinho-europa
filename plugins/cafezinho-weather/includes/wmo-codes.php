<?php
/**
 * Mapeia códigos WMO (Open-Meteo) para ícone + descrição em pt-BR.
 * Códigos desconhecidos caem em fallback genérico.
 */

function cafezinho_wmo_table(): array {
    return [
        0  => [ 'icon' => 'sun',          'label' => 'Sol' ],
        1  => [ 'icon' => 'sun-cloud',    'label' => 'Parcialmente nublado' ],
        2  => [ 'icon' => 'sun-cloud',    'label' => 'Parcialmente nublado' ],
        3  => [ 'icon' => 'cloud',        'label' => 'Nublado' ],
        45 => [ 'icon' => 'fog',          'label' => 'Neblina' ],
        48 => [ 'icon' => 'fog',          'label' => 'Neblina' ],
        51 => [ 'icon' => 'drizzle',      'label' => 'Garoa' ],
        53 => [ 'icon' => 'drizzle',      'label' => 'Garoa' ],
        55 => [ 'icon' => 'drizzle',      'label' => 'Garoa' ],
        61 => [ 'icon' => 'rain',         'label' => 'Chuva' ],
        63 => [ 'icon' => 'rain',         'label' => 'Chuva' ],
        65 => [ 'icon' => 'rain',         'label' => 'Chuva' ],
        71 => [ 'icon' => 'snow',         'label' => 'Neve' ],
        73 => [ 'icon' => 'snow',         'label' => 'Neve' ],
        75 => [ 'icon' => 'snow',         'label' => 'Neve' ],
        80 => [ 'icon' => 'shower',       'label' => 'Pancadas' ],
        81 => [ 'icon' => 'shower',       'label' => 'Pancadas' ],
        82 => [ 'icon' => 'shower',       'label' => 'Pancadas' ],
        95 => [ 'icon' => 'thunderstorm', 'label' => 'Trovoada' ],
    ];
}

function cafezinho_wmo_lookup( int $code ): array {
    $table = cafezinho_wmo_table();
    return $table[ $code ] ?? [ 'icon' => 'cloud', 'label' => 'Indefinido' ];
}
