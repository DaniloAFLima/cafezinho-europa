<?php get_header(); ?>

<div style="text-align: center; padding: 120px 5vw;">
    <div style="font-family: 'Fraunces', serif; font-style: italic; font-weight: 700; font-size: clamp(80px, 18vw, 220px); line-height: 1; color: var(--caramelo-deep); font-variation-settings: 'SOFT' 100, 'WONK' 1; letter-spacing: -0.05em;">
        4☕4
    </div>
    <h1 style="font-family: 'Fraunces', serif; font-weight: 600; font-size: 32px; letter-spacing: -0.02em; margin: 20px 0 12px; color: var(--ink); font-variation-settings: 'SOFT' 30;">
        Cafezinho derramado.
    </h1>
    <p style="font-family: 'Newsreader', serif; font-size: 18px; color: var(--ink-soft); max-width: 500px; margin: 0 auto 30px; line-height: 1.5;">
        Essa página não está mais aqui — ou nunca esteve. Mas tem várias outras notícias servidas fresquinhas esperando por você.
    </p>
    <a href="<?php echo esc_url(home_url('/')); ?>" style="display: inline-block; padding: 14px 28px; background: var(--ink); color: var(--bg); text-decoration: none; font-family: 'JetBrains Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.18em;">
        Voltar pra mesa principal
    </a>
</div>

<?php get_footer(); ?>
