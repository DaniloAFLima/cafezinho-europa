<?php get_header(); ?>

<?php while (have_posts()) : the_post();
    $cat = cafezinho_primary_category();
    $cat_name = $cat ? $cat->name : 'Europa';
    $flag_class = cafezinho_country_flag_class($cat_name);
    $source_name = cafezinho_source_name();
    $reading_time = cafezinho_reading_time();
    $thumb_url = get_the_post_thumbnail_url(null, 'cafezinho-hero');
?>

<article class="post" style="max-width:none; padding:0; margin:0;">

    <div class="post-hero">
        <?php if ($thumb_url) : ?>
            <img src="<?php echo esc_url($thumb_url); ?>" alt="">
        <?php endif; ?>
        <div class="post-hero__overlay">
            <div class="stamp">
                <span class="flag <?php echo esc_attr($flag_class); ?>"></span>
                <?php echo esc_html($cat_name); ?>
            </div>
            <h1 class="post-title"><?php the_title(); ?></h1>
            <div class="post-meta">
                <strong>Servido às 07h</strong>
                <span class="dot">·</span>
                <span><?php echo esc_html(get_the_date('d/m/Y')); ?></span>
                <span class="dot">·</span>
                <span><?php echo $reading_time; ?> minutos com seu café</span>
                <?php if ($source_name) : ?>
                    <span class="dot">·</span>
                    <span>Fonte: <?php echo esc_html($source_name); ?></span>
                <?php endif; ?>
            </div>
        </div>
    </div>

    <div class="post-body">
        <?php the_content(); ?>

        <!-- tags -->
        <?php
        $tags = get_the_tags();
        if (!empty($tags)) : ?>
            <div class="tags">
                <span class="tags__label">Marcado com</span>
                <?php foreach ($tags as $t) : ?>
                    <a href="<?php echo esc_url(get_tag_link($t->term_id)); ?>" class="tag"><?php echo esc_html($t->name); ?></a>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>

        <!-- newsletter inline -->
        <div class="inline-newsletter">
            <h3>Não perca o <span class="accent">cafezinho de amanhã</span></h3>
            <p>Receba todo dia às 07h um resumo das principais notícias da Europa em português, direto no seu email. De graça.</p>
            <form onsubmit="return false">
                <input type="email" placeholder="seu@email.com">
                <button type="submit">Quero o cafezinho</button>
            </form>
        </div>
    </div>

    <!-- related -->
    <?php
    $related = new WP_Query([
        'category__in'        => wp_get_post_categories(get_the_ID()),
        'post__not_in'        => [get_the_ID()],
        'posts_per_page'      => 3,
        'ignore_sticky_posts' => true,
        'orderby'             => 'date',
    ]);
    if ($related->have_posts()) : ?>
        <div class="related">
            <h3 class="related-title">Também na mesa de hoje</h3>
            <div class="related-grid">
                <?php while ($related->have_posts()) : $related->the_post();
                    $rcat = cafezinho_primary_category();
                    $rcat_name = $rcat ? $rcat->name : 'Europa';
                    $rflag = cafezinho_country_flag_class($rcat_name);
                    $rthumb = get_the_post_thumbnail_url(null, 'cafezinho-thumb');
                ?>
                    <article class="rel-card">
                        <a href="<?php the_permalink(); ?>" aria-label="<?php the_title_attribute(); ?>">
                            <div class="rel-card__image">
                                <?php if ($rthumb) : ?>
                                    <img src="<?php echo esc_url($rthumb); ?>" alt="">
                                <?php endif; ?>
                                <div class="stamp">
                                    <span class="flag <?php echo esc_attr($rflag); ?>"></span>
                                    <?php echo esc_html($rcat_name); ?>
                                </div>
                            </div>
                        </a>
                        <h3 class="rel-card__title">
                            <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                        </h3>
                        <div class="rel-card__meta">
                            <?php echo esc_html($rcat_name); ?> · <?php echo cafezinho_reading_time(); ?> min
                        </div>
                    </article>
                <?php endwhile; wp_reset_postdata(); ?>
            </div>
        </div>
    <?php endif; ?>

</article>

<?php endwhile; ?>

<?php get_footer(); ?>
