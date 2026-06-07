<?php
/**
 * Cafezinho Europa — theme functions
 */

if (!defined('ABSPATH')) { exit; }

/* ───── Theme support ───── */
function cafezinho_setup() {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('automatic-feed-links');
    add_theme_support('html5', ['search-form', 'comment-form', 'gallery', 'caption']);
    add_theme_support('responsive-embeds');

    // tamanhos de thumbnail customizados
    set_post_thumbnail_size(800, 600, true);     // padrão
    add_image_size('cafezinho-hero', 1600, 900, true);  // hero da home
    add_image_size('cafezinho-card', 800, 600, true);   // cards da grade
    add_image_size('cafezinho-thumb', 400, 300, true);  // related posts

    // menus
    register_nav_menus([
        'primary' => __('Menu principal (países)', 'cafezinho'),
        'footer'  => __('Menu do rodapé', 'cafezinho'),
    ]);
}
add_action('after_setup_theme', 'cafezinho_setup');

/* ───── Enqueue styles + Google Fonts ───── */
function cafezinho_enqueue_assets() {
    $theme_uri = get_template_directory_uri();
    $version   = wp_get_theme()->get('Version');

    // Google Fonts
    wp_enqueue_style(
        'cafezinho-fonts',
        'https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,300..900,0..100,0..1;1,9..144,300..900,0..100,0..1&family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&family=JetBrains+Mono:wght@400;500&display=swap',
        [],
        null
    );

    wp_enqueue_style('cafezinho-main', $theme_uri . '/assets/main.css', ['cafezinho-fonts'], $version);
}
add_action('wp_enqueue_scripts', 'cafezinho_enqueue_assets');

/* ───── Preconnect para Google Fonts (performance) ───── */
function cafezinho_preconnect() {
    echo '<link rel="preconnect" href="https://fonts.googleapis.com">' . "\n";
    echo '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n";
}
add_action('wp_head', 'cafezinho_preconnect', 1);

/* ───── Mapa categoria → classe CSS da bandeira ───── */
function cafezinho_country_flag_class($category_name) {
    $map = [
        'Suécia'      => 'se',
        'França'      => 'fr',
        'Alemanha'    => 'de',
        'Espanha'     => 'es',
        'Itália'      => 'it',
        'Reino Unido' => 'uk',
        'Europa'      => 'eu',
        'Mundo'       => 'world',
    ];
    return $map[$category_name] ?? 'eu';
}

/* ───── Pega a primeira categoria do post (a "principal") ───── */
function cafezinho_primary_category($post_id = null) {
    $cats = get_the_category($post_id);
    if (empty($cats)) return null;
    return $cats[0];
}

/* ───── Pega o source name do conteúdo (Fonte: XYZ) — fallback ───── */
function cafezinho_source_name($post_id = null) {
    $content = get_post_field('post_content', $post_id);
    if (preg_match('/Fonte:\s*<a[^>]*>([^<]+)<\/a>/i', $content, $m)) {
        return trim($m[1]);
    }
    return '';
}

/* ───── Tempo de leitura estimado (palavras / 200) ───── */
function cafezinho_reading_time($post_id = null) {
    $content = get_post_field('post_content', $post_id);
    $words = str_word_count(wp_strip_all_tags($content));
    $minutes = max(1, (int) ceil($words / 200));
    return $minutes;
}

/* ───── Esconder a barra de admin pra visitantes (UX limpo) ───── */
add_filter('show_admin_bar', function() {
    return current_user_can('edit_posts');
});

/* ───── Customizar excerpt (resumo curto da home) ───── */
function cafezinho_excerpt_length($length) { return 25; }
add_filter('excerpt_length', 'cafezinho_excerpt_length', 999);

function cafezinho_excerpt_more($more) { return '…'; }
add_filter('excerpt_more', 'cafezinho_excerpt_more');

/* ───── Remover emoji bloat ───── */
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('wp_print_styles', 'print_emoji_styles');

/* ───── Banner com data atual + clima fake (decorativo) ───── */
function cafezinho_banner_data() {
    $dias = ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado'];
    $meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
              'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
    $hoje = current_time('timestamp');
    $dia_semana = $dias[(int) date('w', $hoje)];
    $mes = $meses[(int) date('n', $hoje) - 1];
    return sprintf('%s, %s de %s, %s',
        $dia_semana,
        date('d', $hoje),
        $mes,
        date('Y', $hoje)
    );
}
