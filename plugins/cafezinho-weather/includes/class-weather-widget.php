<?php
/**
 * Renderiza o strip de tempo dentro do banner editorial.
 * Função pública: cafezinho_render_weather_bar()
 */
class Cafezinho_Weather_Widget {

    public const DEFAULT_CITY = 'paris';

    public static function render(): void {
        // Garante CSS/JS do widget mesmo quando o tema chama a função
        // diretamente (auto-inject desligado). wp_enqueue_* é idempotente.
        if ( function_exists( 'wp_enqueue_style' ) ) {
            wp_enqueue_style( 'cafezinho-weather' );
            wp_enqueue_script( 'cafezinho-weather' );
        }

        $cached = Cafezinho_Weather_Cache::get();
        if ( $cached === null || empty( $cached['cities'] ) ) {
            self::render_placeholder();
            self::schedule_immediate_refresh();
            return;
        }

        $cities         = require CAFEZINHO_WEATHER_PATH . 'config/cities.php';
        $highlight_slug = self::determine_highlight_slug( $cities );
        $updated_label  = self::format_updated( (int) ( $cached['updated_at'] ?? 0 ) );
        ?>
        <div class="cw" id="cw">
            <div class="cw__strip" role="tablist" aria-label="Tempo nas capitais europeias">
                <span class="cw__supra">Tempo hoje</span>
                <?php foreach ( $cities as $slug => $cfg ) :
                    if ( ! isset( $cached['cities'][ $slug ] ) ) { continue; }
                    $city  = $cached['cities'][ $slug ];
                    $today = $city['days'][0] ?? null;
                    if ( ! $today ) { continue; }
                    $payload = wp_json_encode( self::city_payload( $cfg, $city, $updated_label ) );
                    ?>
                    <button
                        type="button"
                        class="cw__tab"
                        role="tab"
                        data-slug="<?php echo esc_attr( $slug ); ?>"
                        data-payload="<?php echo esc_attr( $payload ); ?>"
                        aria-controls="cw-panel"
                        aria-selected="false"
                        aria-label="<?php echo esc_attr( $cfg['city'] . ' ' . (int) $today['max'] . ' graus' ); ?>">
                        <span class="flag <?php echo esc_attr( $cfg['flag'] ); ?>"></span>
                        <span class="cw__temp"><?php echo (int) $today['max']; ?>°</span>
                    </button>
                <?php endforeach; ?>
            </div>

            <div class="cw__panel"
                 id="cw-panel"
                 role="region"
                 aria-live="polite"
                 data-open="false"
                 data-default-slug="<?php echo esc_attr( $highlight_slug ); ?>">
                <!-- Painel populado por weather.js no primeiro clique -->
            </div>
        </div>
        <?php
    }

    /**
     * Estrutura serializada em data-payload de cada aba para o JS hidratar o painel.
     */
    private static function city_payload( array $cfg, array $city, string $updated_label ): array {
        $days = [];
        foreach ( $city['days'] as $i => $day ) {
            $wmo    = cafezinho_wmo_lookup( (int) $day['code'] );
            $days[] = [
                'label'   => self::day_label( $i, $day['date'] ),
                'max'     => (int) $day['max'],
                'min'     => (int) $day['min'],
                'icon'    => $wmo['icon'],
                'desc'    => $wmo['label'],
            ];
        }
        return [
            'country' => self::country_code( $cfg['flag'] ),
            'city'    => $cfg['city'],
            'updated' => $updated_label,
            'days'    => $days,
        ];
    }

    private static function country_code( string $flag_slug ): string {
        $map = [ 'gb' => 'GB', 'uk' => 'GB', 'fr' => 'FR', 'de' => 'DE',
                 'es' => 'ES', 'it' => 'IT', 'se' => 'SE' ];
        return $map[ strtolower( $flag_slug ) ] ?? strtoupper( $flag_slug );
    }

    private static function format_updated( int $unix ): string {
        if ( $unix <= 0 ) return 'Atualizado agora';
        return 'Atualizado às ' . gmdate( 'H:i', $unix ) . ' UTC';
    }

    private static function render_placeholder(): void {
        ?>
        <div class="cw cw--placeholder">
            <span class="cw__supra cw__supra--solo">Tempo carregando…</span>
        </div>
        <?php
    }

    private static function schedule_immediate_refresh(): void {
        $next = wp_next_scheduled( Cafezinho_Weather_Cron::HOOK );
        if ( ! $next || $next > time() + 30 ) {
            wp_schedule_single_event( time(), Cafezinho_Weather_Cron::HOOK );
        }
    }

    /**
     * Cidade-destaque (usada como default-slug se o JS implementar um botão "abrir").
     * Não abre painel automaticamente — abertura é sempre por clique do leitor.
     */
    private static function determine_highlight_slug( array $cities ): string {
        if ( function_exists( 'is_category' ) && is_category() ) {
            $cat = single_cat_title( '', false );
            foreach ( $cities as $slug => $cfg ) {
                if ( strcasecmp( $cat, $cfg['country'] ) === 0 ) {
                    return $slug;
                }
            }
        }
        $default = apply_filters( 'cafezinho_weather_default_city', self::DEFAULT_CITY );
        return isset( $cities[ $default ] ) ? $default : array_key_first( $cities );
    }

    private static function day_label( int $index, string $iso_date ): string {
        $weekdays = [ 'Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb' ];
        $w = (int) date( 'w', strtotime( $iso_date ) );
        $wd = $weekdays[ $w ] ?? '';
        if ( $index === 0 ) return $wd ? "Hoje · $wd" : 'Hoje';
        if ( $index === 1 ) return 'Amanhã';
        return $wd;
    }
}

function cafezinho_render_weather_bar(): void {
    Cafezinho_Weather_Widget::render();
}
