<?php get_header(); ?>

<?php
// Pega os posts: 1 hero + 6 cards = 7 mais recentes
$query = new WP_Query([
    'post_status'    => 'publish',
    'posts_per_page' => 7,
    'ignore_sticky_posts' => true,
]);

if (!$query->have_posts()) {
    echo '<p style="text-align:center; font-style:italic; padding: 80px 0; color:var(--ink-soft);">Ainda não saiu o cafezinho de hoje — volta em alguns minutos.</p>';
    get_footer();
    return;
}

$is_first = true;
?>

<div class="home-layout">
<div class="main-feed">

<?php while ($query->have_posts()) : $query->the_post();
    $cat = cafezinho_primary_category();
    $cat_name = $cat ? $cat->name : 'Europa';
    $flag_class = cafezinho_country_flag_class($cat_name);
    $source_name = cafezinho_source_name();
    $reading_time = cafezinho_reading_time();
    $thumb_url = get_the_post_thumbnail_url(null, 'cafezinho-hero');
?>

    <?php if ($is_first) : $is_first = false; ?>

        <!-- HERO: primeiro post -->
        <article class="hero">
            <div class="hero__image">
                <?php if ($thumb_url) : ?>
                    <a href="<?php the_permalink(); ?>" aria-label="<?php the_title_attribute(); ?>">
                        <img src="<?php echo esc_url($thumb_url); ?>" alt="">
                    </a>
                <?php endif; ?>
                <div class="stamp">
                    <span class="flag <?php echo esc_attr($flag_class); ?>"></span>
                    <?php echo esc_html($cat_name); ?>
                </div>
            </div>
            <div class="hero__meta">
                <div class="kicker hero__kicker">
                    Manchete do dia · <?php echo $reading_time; ?> min com seu café
                </div>
                <h2 class="hero__title">
                    <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                </h2>
                <p class="hero__dek"><?php echo esc_html(wp_trim_words(get_the_excerpt(), 36, '…')); ?></p>
                <div class="byline">
                    <span>Resumo do Cafezinho</span>
                    <span class="dot">•</span>
                    <?php if ($source_name) : ?>
                        <span>Fonte: <?php echo esc_html($source_name); ?></span>
                        <span class="dot">•</span>
                    <?php endif; ?>
                    <span><?php echo esc_html(human_time_diff(get_the_time('U'), current_time('timestamp'))); ?> atrás</span>
                </div>
            </div>
        </article>

        <h3 class="section-title">Servido fresquinho</h3>
        <div class="grid">

    <?php else : ?>

        <!-- CARD -->
        <article class="card">
            <a class="card__image-link" href="<?php the_permalink(); ?>" aria-label="<?php the_title_attribute(); ?>">
                <div class="card__image">
                    <?php if ($thumb_url) : ?>
                        <img src="<?php echo esc_url($thumb_url); ?>" alt="">
                    <?php endif; ?>
                    <div class="stamp">
                        <span class="flag <?php echo esc_attr($flag_class); ?>"></span>
                        <?php echo esc_html($cat_name); ?>
                    </div>
                </div>
            </a>
            <div class="card__kicker"><?php echo esc_html($cat_name); ?> · <?php echo $reading_time; ?> min</div>
            <h2 class="card__title">
                <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
            </h2>
            <p class="card__dek"><?php echo esc_html(wp_trim_words(get_the_excerpt(), 22, '…')); ?></p>
            <div class="card__meta">
                <span><?php echo esc_html(human_time_diff(get_the_time('U'), current_time('timestamp'))); ?> atrás</span>
                <?php if ($source_name) : ?>
                    · <span class="source"><?php echo esc_html($source_name); ?></span>
                <?php endif; ?>
            </div>
        </article>

    <?php endif; ?>

<?php endwhile; ?>

        </div><!-- /.grid -->

<!-- decorative divider -->
<div class="coffee-stain" aria-hidden="true">
    <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
        <circle cx="40" cy="40" r="32" fill="none" stroke="#B86A1C" stroke-width="1.5" opacity="0.5"/>
        <circle cx="40" cy="40" r="28" fill="none" stroke="#B86A1C" stroke-width="0.8" opacity="0.3"/>
        <circle cx="40" cy="40" r="34" fill="none" stroke="#B86A1C" stroke-width="0.4" opacity="0.2" stroke-dasharray="2 1"/>
    </svg>
</div>

</div><!-- /.main-feed -->

<?php
// Sidebar: última crônica da coluna "Cafezinho & Planeta, Urgente!"
$cronica_cat = get_category_by_slug('cafezinho-planeta-urgente');
if (!$cronica_cat) {
    // Tenta por nome exato caso o slug gerado seja diferente
    $cronica_cat_obj = get_term_by('name', 'Cafezinho & Planeta, Urgente!', 'category');
    if ($cronica_cat_obj) {
        $cronica_cat = $cronica_cat_obj;
    }
}
$cronica_posts = [];
if ($cronica_cat) {
    $cronica_query = new WP_Query([
        'post_status'    => 'publish',
        'posts_per_page' => 1,
        'cat'            => $cronica_cat->term_id,
    ]);
    if ($cronica_query->have_posts()) {
        $cronica_query->the_post();
        $cronica_posts[] = [
            'title'   => get_the_title(),
            'excerpt' => wp_trim_words(get_the_excerpt(), 28, '…'),
            'url'     => get_the_permalink(),
            'date'    => get_the_date('d/m/Y'),
        ];
        wp_reset_postdata();
    }
}
?>

<aside class="home-sidebar" aria-label="Coluna da semana">
    <div class="sidebar-cronica">
        <div class="sidebar-cronica__header">
            <span class="sidebar-cronica__globe" aria-hidden="true">
                <svg width="22" height="22" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="40" cy="40" r="36" fill="none" stroke="currentColor" stroke-width="4"/>
                    <ellipse cx="40" cy="40" rx="36" ry="16" fill="none" stroke="currentColor" stroke-width="3"/>
                    <line x1="4" y1="40" x2="76" y2="40" stroke="currentColor" stroke-width="3"/>
                    <line x1="40" y1="4" x2="40" y2="76" stroke="currentColor" stroke-width="3"/>
                    <path d="M40,4 Q60,40 40,76" fill="none" stroke="currentColor" stroke-width="2"/>
                    <path d="M40,4 Q20,40 40,76" fill="none" stroke="currentColor" stroke-width="2"/>
                </svg>
            </span>
            <div>
                <div class="sidebar-cronica__label">Coluna da semana</div>
                <div class="sidebar-cronica__name">Cafezinho &amp; Planeta, Urgente!</div>
            </div>
        </div>

        <?php if (!empty($cronica_posts)) : $p = $cronica_posts[0]; ?>
            <a class="sidebar-cronica__post" href="<?php echo esc_url($p['url']); ?>">
                <div class="sidebar-cronica__date"><?php echo esc_html($p['date']); ?></div>
                <h3 class="sidebar-cronica__title"><?php echo esc_html($p['title']); ?></h3>
                <p class="sidebar-cronica__dek"><?php echo esc_html($p['excerpt']); ?></p>
                <span class="sidebar-cronica__cta">Ler a crônica →</span>
            </a>
        <?php else : ?>
            <div class="sidebar-cronica__empty">
                <p>A fika ainda não começou — vem domingo com novidades da Europa.</p>
            </div>
        <?php endif; ?>

        <div class="sidebar-cronica__cast" aria-hidden="true">
            <span title="Pedrinho do Mundo">🌶️</span>
            <span title="Raj das Planilhas">🎧</span>
            <span title="Lars Lagom">🇸🇪</span>
            <span title="Zbig">🇵🇱</span>
            <span title="Cafeteira 3000">☕</span>
        </div>
    </div>
</aside>

</div><!-- /.home-layout -->

<?php wp_reset_postdata(); ?>

<?php get_footer(); ?>
