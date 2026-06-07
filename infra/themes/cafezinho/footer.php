</main>

<footer class="site-footer">
    <div class="foot-grid">
        <div>
            <div class="foot-brand">Cafezinho <span class="accent">Europa</span></div>
            <div class="foot-tag">
                Notícias da Europa em português do Brasil, servidas fresquinhas todo dia às 07h. Como aquele cafezinho que você toma antes de encarar o mundo.
            </div>
        </div>
        <div class="foot-col">
            <h4>Editoria</h4>
            <a href="<?php echo esc_url(home_url('/sobre')); ?>">Sobre o site</a>
            <a href="<?php echo esc_url(home_url('/como-funciona')); ?>">Como funciona</a>
            <a href="<?php echo esc_url(home_url('/politica-editorial')); ?>">Política editorial</a>
            <a href="<?php echo esc_url(home_url('/contato')); ?>">Contato</a>
        </div>
        <div class="foot-col">
            <h4>Países</h4>
            <?php
            $countries = ['Suécia', 'França', 'Alemanha', 'Espanha', 'Itália', 'Reino Unido'];
            foreach ($countries as $country) {
                $cat = get_category_by_slug(sanitize_title($country));
                if ($cat) {
                    printf(
                        '<a href="%s">%s</a>',
                        esc_url(get_category_link($cat->term_id)),
                        esc_html($country)
                    );
                }
            }
            ?>
        </div>
        <div class="foot-col">
            <h4>Siga</h4>
            <a href="<?php echo esc_url(home_url('/feed')); ?>">RSS</a>
            <a href="#">Newsletter diária</a>
            <a href="#">Telegram</a>
            <a href="#">Instagram</a>
        </div>
    </div>
    <div class="foot-base">
        <div>© <?php echo esc_html(date('Y')); ?> Cafezinho Europa · Conteúdo agregado com créditos às fontes citadas</div>
        <div>Servido com ❤ em pt-BR</div>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
