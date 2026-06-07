<?php
require_once __DIR__ . '/../vendor/autoload.php';

if ( ! defined( 'ABSPATH' ) ) {
    define( 'ABSPATH', __DIR__ . '/../' );
}

// Stubs para funções do WordPress usadas nos caminhos testados por unidade.
if ( ! function_exists( 'get_transient' ) ) {
    $GLOBALS['__cw_transients'] = [];
    function get_transient( $key ) {
        return $GLOBALS['__cw_transients'][ $key ] ?? false;
    }
    function set_transient( $key, $value, $ttl = 0 ) {
        $GLOBALS['__cw_transients'][ $key ] = $value;
        return true;
    }
    function delete_transient( $key ) {
        unset( $GLOBALS['__cw_transients'][ $key ] );
        return true;
    }
}

if ( ! function_exists( 'esc_html' ) ) {
    function esc_html( $s ) { return htmlspecialchars( (string) $s, ENT_QUOTES, 'UTF-8' ); }
    function esc_attr( $s ) { return htmlspecialchars( (string) $s, ENT_QUOTES, 'UTF-8' ); }
}
