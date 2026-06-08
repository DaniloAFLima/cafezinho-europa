<?php
/**
 * Página admin em Configurações → Cafezinho Weather.
 */
class Cafezinho_Weather_Admin {

    public const MENU_SLUG = 'cafezinho-weather';

    public static function register_menu(): void {
        add_options_page(
            'Cafezinho Weather',
            'Cafezinho Weather',
            'manage_options',
            self::MENU_SLUG,
            [ __CLASS__, 'render_page' ]
        );
    }

    public static function handle_actions(): void {
        if ( ! current_user_can( 'manage_options' ) ) {
            return;
        }
        if ( ! isset( $_POST['cw_action'] ) || ! check_admin_referer( 'cw_admin_action' ) ) {
            return;
        }
        $action = sanitize_text_field( $_POST['cw_action'] );
        if ( $action === 'refresh' ) {
            Cafezinho_Weather_Cron::handle_refresh();
            add_action( 'admin_notices', function () {
                echo '<div class="notice notice-success"><p>Refresh disparado.</p></div>';
            } );
        } elseif ( $action === 'clear' ) {
            Cafezinho_Weather_Cache::clear();
            add_action( 'admin_notices', function () {
                echo '<div class="notice notice-success"><p>Cache limpo.</p></div>';
            } );
        }
    }

    public static function render_page(): void {
        $cached    = Cafezinho_Weather_Cache::get();
        $cities    = require CAFEZINHO_WEATHER_PATH . 'config/cities.php';
        $failures  = (int) get_option( Cafezinho_Weather_Cron::FAILURE_KEY, 0 );
        $next_run  = wp_next_scheduled( Cafezinho_Weather_Cron::HOOK );
        ?>
        <div class="wrap">
            <h1>Cafezinho Weather</h1>

            <?php if ( $failures >= 6 ) : ?>
                <div class="notice notice-error">
                    <p><strong><?php echo (int) $failures; ?> falhas consecutivas.</strong> Verifique conectividade com Open-Meteo.</p>
                </div>
            <?php endif; ?>

            <h2>Status</h2>
            <table class="widefat striped" style="max-width:700px">
                <tbody>
                    <tr>
                        <th>Última atualização</th>
                        <td><?php echo $cached ? esc_html( gmdate( 'Y-m-d H:i:s', $cached['updated_at'] ) . ' UTC' ) : '<em>nunca</em>'; ?></td>
                    </tr>
                    <tr>
                        <th>Próximo cron</th>
                        <td><?php echo $next_run ? esc_html( gmdate( 'Y-m-d H:i:s', $next_run ) . ' UTC' ) : '<em>não agendado</em>'; ?></td>
                    </tr>
                    <tr>
                        <th>Falhas consecutivas</th>
                        <td><?php echo (int) $failures; ?></td>
                    </tr>
                </tbody>
            </table>

            <h2>Cidades</h2>
            <table class="widefat striped" style="max-width:700px">
                <thead>
                    <tr><th>Slug</th><th>Cidade</th><th>Última leitura</th><th>Hoje (máx/mín)</th></tr>
                </thead>
                <tbody>
                    <?php foreach ( $cities as $slug => $cfg ) :
                        $city = $cached['cities'][ $slug ] ?? null; ?>
                        <tr>
                            <td><code><?php echo esc_html( $slug ); ?></code></td>
                            <td><?php echo esc_html( $cfg['city'] ); ?></td>
                            <td><?php echo $city ? esc_html( gmdate( 'Y-m-d H:i:s', $city['fetched_at'] ) . ' UTC' ) : '<em style="color:#a00">— em fallback</em>'; ?></td>
                            <td><?php echo $city ? esc_html( $city['days'][0]['max'] . '°/' . $city['days'][0]['min'] . '°' ) : '—'; ?></td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>

            <h2>Ações</h2>
            <form method="post" style="display:inline">
                <?php wp_nonce_field( 'cw_admin_action' ); ?>
                <input type="hidden" name="cw_action" value="refresh" />
                <button type="submit" class="button button-primary">Atualizar agora</button>
            </form>
            <form method="post" style="display:inline; margin-left:8px">
                <?php wp_nonce_field( 'cw_admin_action' ); ?>
                <input type="hidden" name="cw_action" value="clear" />
                <button type="submit" class="button">Limpar cache</button>
            </form>
        </div>
        <?php
    }
}
