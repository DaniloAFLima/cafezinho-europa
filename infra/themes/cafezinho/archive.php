<?php get_header(); ?>

<?php
$is_category = is_category();
$is_tag = is_tag();
$title = '';
$flag_class = 'eu';

if ($is_category) {
    $title = single_cat_title('', false);
    $flag_class = cafezinho_country_flag_class($title);
} elseif ($is_tag) {
    $title = single_tag_title('', false);
}
?>

<div class="archive-header">
    <?php if ($is_category) : ?>
        <div class="archive-flag flag <?php echo esc_attr($flag_class); ?>"></div>
    <?php endif; ?>
    <h1><?php echo esc_html($title); ?></h1>
    <?php if (category_description() || tag_description()) : ?>
        <p><?php echo wp_kses_post(category_description() . tag_description()); ?></p>
    <?php else : ?>
        <p>Tudo que servimos sobre <em><?php echo esc_html($title); ?></em> — fresquinho todo dia.</p>
    <?php endif; ?>
</div>

<?php if (have_posts()) : ?>

    <div class="grid">
        <?php while (have_posts()) : the_post();
            $cat = cafezinho_primary_category();
            $cat_name = $cat ? $cat->name : 'Europa';
            $f = cafezinho_country_flag_class($cat_name);
            $source = cafezinho_source_name();
            $rt = cafezinho_reading_time();
            $thumb = get_the_post_thumbnail_url(null, 'cafezinho-card');
        ?>
            <article class="card">
                <a class="card__image-link" href="<?php the_permalink(); ?>" aria-label="<?php the_title_attribute(); ?>">
                    <div class="card__image">
                        <?php if ($thumb) : ?>
                            <img src="<?php echo esc_url($thumb); ?>" alt="">
                        <?php endif; ?>
                        <div class="stamp">
                            <span class="flag <?php echo esc_attr($f); ?>"></span>
                            <?php echo esc_html($cat_name); ?>
                        </div>
                    </div>
                </a>
                <div class="card__kicker"><?php echo esc_html($cat_name); ?> · <?php echo $rt; ?> min</div>
                <h2 class="card__title">
                    <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                </h2>
                <p class="card__dek"><?php echo esc_html(wp_trim_words(get_the_excerpt(), 22, '…')); ?></p>
                <div class="card__meta">
                    <span><?php echo esc_html(get_the_date('d/m/Y')); ?></span>
                    <?php if ($source) : ?>
                        · <span class="source"><?php echo esc_html($source); ?></span>
                    <?php endif; ?>
                </div>
            </article>
        <?php endwhile; ?>
    </div>

    <div style="text-align:center; margin-top: 60px; font-family: 'JetBrains Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.16em;">
        <?php
        the_posts_pagination([
            'mid_size' => 1,
            'prev_text' => '← Anterior',
            'next_text' => 'Próximo →',
        ]);
        ?>
    </div>

<?php else : ?>

    <p style="text-align:center; font-style:italic; padding: 80px 0; color: var(--ink-soft);">
        Nada por enquanto nessa seção. Volte em alguns dias.
    </p>

<?php endif; ?>

<?php get_footer(); ?>
