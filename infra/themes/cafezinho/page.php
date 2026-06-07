<?php get_header(); ?>

<?php while (have_posts()) : the_post(); ?>

    <div class="post-body" style="padding-top: 60px;">
        <h1 style="font-family: 'Fraunces', serif; font-weight: 700; font-size: clamp(36px, 5vw, 56px); line-height: 1; letter-spacing: -0.03em; margin-bottom: 30px; color: var(--ink); font-variation-settings: 'SOFT' 30, 'WONK' 0;">
            <?php the_title(); ?>
        </h1>

        <?php the_content(); ?>
    </div>

<?php endwhile; ?>

<?php get_footer(); ?>
