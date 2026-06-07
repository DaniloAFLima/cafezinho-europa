<?php
/**
 * Plugin Name: Cafezinho Weather
 * Description: Widget editorial de previsão do tempo para os 6 países cobertos pelo Cafezinho Europa.
 * Version:     0.1.0
 * Author:      Cafezinho Europa
 * License:     MIT
 * Requires PHP: 8.1
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

define( 'CAFEZINHO_WEATHER_VERSION', '0.1.0' );
define( 'CAFEZINHO_WEATHER_PATH', plugin_dir_path( __FILE__ ) );
define( 'CAFEZINHO_WEATHER_URL', plugin_dir_url( __FILE__ ) );

require_once CAFEZINHO_WEATHER_PATH . 'includes/wmo-codes.php';
require_once CAFEZINHO_WEATHER_PATH . 'includes/class-weather-fetcher.php';
require_once CAFEZINHO_WEATHER_PATH . 'includes/class-weather-cache.php';
require_once CAFEZINHO_WEATHER_PATH . 'includes/class-weather-cron.php';
require_once CAFEZINHO_WEATHER_PATH . 'includes/class-weather-widget.php';
require_once CAFEZINHO_WEATHER_PATH . 'includes/class-weather-admin.php';

// Cron schedule + handler.
add_filter( 'cron_schedules', [ 'Cafezinho_Weather_Cron', 'register_schedule' ] );
add_action( Cafezinho_Weather_Cron::HOOK, [ 'Cafezinho_Weather_Cron', 'handle_refresh' ] );

// Activation / deactivation.
register_activation_hook( __FILE__, [ 'Cafezinho_Weather_Cron', 'on_activate' ] );
register_deactivation_hook( __FILE__, [ 'Cafezinho_Weather_Cron', 'on_deactivate' ] );

// Register front-end assets (fonts + plugin css/js).
add_action( 'wp_enqueue_scripts', function () {
    wp_register_style(
        'cafezinho-weather-fonts',
        'https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,300..900,0..100,0..1;1,9..144,300..900,0..100,0..1&family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&family=JetBrains+Mono:wght@400;500&display=swap',
        [],
        null
    );
    wp_register_style(
        'cafezinho-weather',
        CAFEZINHO_WEATHER_URL . 'assets/weather.css',
        [ 'cafezinho-weather-fonts' ],
        CAFEZINHO_WEATHER_VERSION
    );
    wp_register_script(
        'cafezinho-weather',
        CAFEZINHO_WEATHER_URL . 'assets/weather.js',
        [],
        CAFEZINHO_WEATHER_VERSION,
        true
    );
} );

/**
 * Indica se devemos auto-injetar um banner completo (data + edição + widget).
 * Tema custom: define constante ou retorna false no filtro.
 */
function cafezinho_weather_should_auto_inject(): bool {
    if ( defined( 'CAFEZINHO_WEATHER_NO_AUTO' ) && CAFEZINHO_WEATHER_NO_AUTO ) {
        return false;
    }
    return (bool) apply_filters( 'cafezinho_weather_auto_banner', true );
}

/**
 * Banner editorial completo — só renderizado em temas sem integração própria.
 */
function cafezinho_weather_render_fallback_banner(): void {
    if ( ! cafezinho_weather_should_auto_inject() ) {
        return;
    }
    wp_enqueue_style( 'cafezinho-weather' );
    wp_enqueue_script( 'cafezinho-weather' );

    $months = [ '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro' ];
    $weekdays = [ 'Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado' ];
    $now = current_time( 'timestamp' );
    $date_str = sprintf(
        '%s, <span>%02d de %s, %d</span>',
        $weekdays[ (int) gmdate( 'w', $now ) ],
        (int) gmdate( 'j', $now ),
        $months[ (int) gmdate( 'n', $now ) ],
        (int) gmdate( 'Y', $now )
    );
    ?>
    <style>
    .cw-banner {
        border-bottom: 1px solid var(--ink, #2A1812);
        padding: 14px 5vw;
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        gap: 24px;
        font-family: 'JetBrains Mono', ui-monospace, monospace;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--ink-soft, #5A3F35);
        background: var(--bg, #FAF6F0);
    }
    .cw-banner__date span { color: var(--caramelo-deep, #8C4F12); font-weight: 500; }
    .cw-banner__edition { text-align: center; }
    @media (max-width: 768px) {
        .cw-banner { grid-template-columns: 1fr; text-align: center; gap: 6px; padding: 10px 5vw; }
    }
    </style>
    <div class="cw-banner">
        <div class="cw-banner__date"><?php echo wp_kses_post( $date_str ); ?></div>
        <div class="cw-banner__edition">Edição diária</div>
        <?php cafezinho_render_weather_bar(); ?>
    </div>
    <?php
}

// Auto-inject the complete banner when no custom theme has wired things up.
add_action( 'wp_body_open', 'cafezinho_weather_render_fallback_banner' );

// Admin page.
add_action( 'admin_menu', [ 'Cafezinho_Weather_Admin', 'register_menu' ] );
add_action( 'admin_init', [ 'Cafezinho_Weather_Admin', 'handle_actions' ] );
