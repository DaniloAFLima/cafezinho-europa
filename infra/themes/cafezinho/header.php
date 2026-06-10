<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#2A1812">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>

<?php if (is_front_page() || is_home()) : ?>

    <!-- top banner editorial -->
    <div class="banner">
        <div class="banner__date">
            <?php echo esc_html(cafezinho_banner_data()); ?>
        </div>
        <div class="banner__edition">
            Servido todo dia às 07h UTC
        </div>
        <?php if ( function_exists( 'cafezinho_render_weather_bar' ) ) : ?>
            <?php cafezinho_render_weather_bar(); ?>
        <?php else : ?>
            <div class="banner__motto"><em>Notícias da Europa, em português</em></div>
        <?php endif; ?>
    </div>

    <!-- masthead grande (só na home) -->
    <header class="masthead">
        <div class="masthead__supra">Notícias da Europa</div>
        <h1 class="wordmark">
            <a href="<?php echo esc_url(home_url('/')); ?>">
                Cafez<span class="wm-steam-i">ı<svg class="wm-steam" viewBox="0 0 20 56" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><circle class="wm-dot" cx="10" cy="52" r="3" fill="currentColor"/><path class="s1" d="M8 46 Q4 34 8 22 Q12 10 8 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" pathLength="1"/><path class="s2" d="M12 46 Q16 34 12 22 Q8 10 12 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" pathLength="1"/></svg></span>nho<span class="accent">Europa</span>
            </a>
        </h1>
        <div class="masthead__rule"></div>
        <div class="masthead__infra">Servido todo dia às 07h</div>

        <div class="seal" aria-hidden="true">
            <div class="seal__text">Servido<br>às</div>
            <div class="seal__time">07h</div>
            <div class="seal__text">UTC · diário</div>
        </div>
    </header>

<?php else : ?>

    <!-- compact header nas internas -->
    <div class="banner">
        <div class="banner__date" style="text-align:left">
            <a href="<?php echo esc_url(home_url('/')); ?>" style="font-family:'Fraunces',serif;font-style:italic;font-weight:600;font-size:18px;text-transform:none;letter-spacing:-0.01em;color:var(--ink);text-decoration:none;font-variation-settings:'SOFT' 80,'WONK' 1;">
                Cafezinho <span style="color:var(--caramelo-deep)">Europa</span>
            </a>
        </div>
        <div class="banner__edition"><?php echo esc_html(cafezinho_banner_data()); ?></div>
        <?php if ( function_exists( 'cafezinho_render_weather_bar' ) ) : ?>
            <?php cafezinho_render_weather_bar(); ?>
        <?php else : ?>
            <div class="banner__motto"><em>Notícias da Europa, em português</em></div>
        <?php endif; ?>
    </div>

<?php endif; ?>

<!-- nav de países -->
<nav class="countries" role="navigation">
    <a href="<?php echo esc_url(home_url('/')); ?>" class="<?php echo (is_front_page() || is_home()) ? 'active' : ''; ?>">Manchete</a>
    <?php
    $countries = ['Suécia', 'França', 'Alemanha', 'Espanha', 'Itália', 'Reino Unido', 'Europa', 'Mundo'];
    foreach ($countries as $country) {
        $cat = get_category_by_slug(sanitize_title($country));
        if ($cat) {
            $url = get_category_link($cat->term_id);
            $is_active = (is_category() && single_cat_title('', false) === $country) ? 'active' : '';
            printf(
                '<a href="%s" class="%s">%s</a>',
                esc_url($url),
                esc_attr($is_active),
                esc_html($country)
            );
        } else {
            // se a categoria ainda não existe, link inativo
            printf('<a href="#" style="opacity:0.4">%s</a>', esc_html($country));
        }
    }
    ?>
</nav>

<main class="site-main">
