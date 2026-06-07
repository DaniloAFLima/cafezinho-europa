# Weather Widget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a thin weather bar at the top of the Cafezinho Europa header showing today + next 2 days of weather for the 6 capital cities of the countries covered by the site.

**Architecture:** Standalone WordPress plugin (`cafezinho-weather`) living in the repo at `plugins/cafezinho-weather/` and bind-mounted into the WP container. A WP-Cron event runs every 2h to fetch Open-Meteo data for 6 cities in parallel, stores the result in a transient (3h TTL), and the header template echoes a `cafezinho_render_weather_bar()` function that reads from the transient and renders all 6 cities inline. Tab switching is purely DOM (no front-end network calls). Per-city merge in the cache layer means a single failed city keeps the previous reading instead of disappearing.

**Tech Stack:**
- PHP 8.3 / WordPress 6.7 (already in `infra/docker-compose.yml`)
- PHPUnit 10 for unit tests (no WP test framework — pure-PHP unit tests with stubs)
- Open-Meteo HTTP API (no API key)
- Vanilla CSS + vanilla JS (no framework, no external deps)
- Composer for autoload + PHPUnit only
- Fonts: Fraunces + Newsreader + JetBrains Mono (Google Fonts — already loaded by the theme; plugin assumes their availability)
- Flags: 100% CSS gradients (no image assets)

**Spec:** `docs/superpowers/specs/2026-06-07-weather-widget-design.md`
**Visual reference (interactive mockup):** `design/weather-bar.html`

---

## File Structure

Plugin lives at `plugins/cafezinho-weather/` in the repo. Docker compose will bind-mount it into `/var/www/html/wp-content/plugins/cafezinho-weather`.

```
plugins/cafezinho-weather/
├── cafezinho-weather.php           # bootstrap, register hooks, activation/deactivation
├── composer.json                   # PHPUnit + autoload only
├── includes/
│   ├── class-weather-fetcher.php   # Open-Meteo client + parse_response
│   ├── class-weather-cache.php     # transient get/merge_and_store
│   ├── class-weather-cron.php      # schedule + handler + lock
│   ├── class-weather-widget.php    # cafezinho_render_weather_bar()
│   ├── class-weather-admin.php     # Settings → Cafezinho Weather page
│   └── wmo-codes.php               # WMO code → icon slug + pt-BR description
├── config/
│   └── cities.php                  # 6 cities: slug, country, flag, lat, lon
├── assets/
│   ├── weather.css                 # includes flag gradients + icon SVGs inline
│   └── weather.js
├── tests/
│   ├── bootstrap.php               # WP function stubs for unit tests
│   ├── test-wmo-codes.php
│   ├── test-weather-fetcher.php
│   ├── test-weather-cache.php
│   └── fixtures/
│       └── open-meteo-paris.json
├── bin/
│   └── smoke-weather.php           # CLI: hits real Open-Meteo for all 6 cities
└── phpunit.xml
```

Also modified:
- `infra/docker-compose.yml` (add plugin bind mount)
- `.gitignore` (add `plugins/cafezinho-weather/vendor/`)

---

## Task 1: Plugin scaffolding + Composer + PHPUnit bootstrap

**Files:**
- Create: `plugins/cafezinho-weather/cafezinho-weather.php`
- Create: `plugins/cafezinho-weather/composer.json`
- Create: `plugins/cafezinho-weather/phpunit.xml`
- Create: `plugins/cafezinho-weather/tests/bootstrap.php`
- Modify: `.gitignore`

- [ ] **Step 1: Create plugin main file with WordPress header**

`plugins/cafezinho-weather/cafezinho-weather.php`:

```php
<?php
/**
 * Plugin Name: Cafezinho Weather
 * Description: Barra de previsão do tempo para os 6 países cobertos pelo Cafezinho Europa.
 * Version:     0.1.0
 * Author:      Cafezinho Europa
 * License:     MIT
 * Requires PHP: 8.1
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

define( 'CAFEZINHO_WEATHER_VERSION', '0.1.0' );
define( 'CAFEZINHO_WEATHER_PATH', plugin_dir_path( __FILE__ ) );
define( 'CAFEZINHO_WEATHER_URL', plugin_dir_url( __FILE__ ) );
```

- [ ] **Step 2: Create composer.json**

`plugins/cafezinho-weather/composer.json`:

```json
{
    "name": "cafezinho/weather",
    "description": "Weather widget plugin for Cafezinho Europa.",
    "type": "wordpress-plugin",
    "require": {
        "php": ">=8.1"
    },
    "require-dev": {
        "phpunit/phpunit": "^10.5"
    },
    "autoload": {
        "classmap": ["includes/"]
    },
    "autoload-dev": {
        "classmap": ["tests/"]
    }
}
```

- [ ] **Step 3: Create phpunit.xml**

`plugins/cafezinho-weather/phpunit.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<phpunit
    bootstrap="tests/bootstrap.php"
    colors="true"
    failOnWarning="true"
    failOnRisky="true"
    cacheDirectory=".phpunit.cache">
    <testsuites>
        <testsuite name="unit">
            <directory>tests</directory>
        </testsuite>
    </testsuites>
</phpunit>
```

- [ ] **Step 4: Create test bootstrap with WP function stubs**

`plugins/cafezinho-weather/tests/bootstrap.php`:

```php
<?php
require_once __DIR__ . '/../vendor/autoload.php';

if ( ! defined( 'ABSPATH' ) ) {
    define( 'ABSPATH', __DIR__ . '/../' );
}

// Stubs for WordPress functions used in unit-tested code paths.
if ( ! function_exists( 'get_transient' ) ) {
    $GLOBALS['__cw_transients'] = [];
    function get_transient( $key ) {
        return $GLOBALS['__cw_transients'][ $key ] ?? false;
    }
    function set_transient( $key, $value, $ttl = 0 ) {
        $GLOBALS['__cw_transients'][ $key ] = $value;
        return true;
    }
    function delete_transient( $key ) {
        unset( $GLOBALS['__cw_transients'][ $key ] );
        return true;
    }
}

if ( ! function_exists( 'esc_html' ) ) {
    function esc_html( $s ) { return htmlspecialchars( (string) $s, ENT_QUOTES, 'UTF-8' ); }
    function esc_attr( $s ) { return htmlspecialchars( (string) $s, ENT_QUOTES, 'UTF-8' ); }
}
```

- [ ] **Step 5: Add vendor/ and .phpunit.cache/ to .gitignore**

Modify `.gitignore` — append:

```
# WordPress plugin dev artifacts
plugins/cafezinho-weather/vendor/
plugins/cafezinho-weather/.phpunit.cache/
plugins/cafezinho-weather/composer.lock
```

- [ ] **Step 6: Install Composer dependencies**

Run from `plugins/cafezinho-weather/`:

```
composer install
```

Expected: creates `vendor/`, `composer.lock`. No errors.

- [ ] **Step 7: Smoke-run PHPUnit (no tests yet)**

Run from `plugins/cafezinho-weather/`:

```
vendor/bin/phpunit
```

Expected: `No tests executed!` exits 0. Confirms the harness is wired.

- [ ] **Step 8: Commit**

```
git add plugins/cafezinho-weather/cafezinho-weather.php plugins/cafezinho-weather/composer.json plugins/cafezinho-weather/phpunit.xml plugins/cafezinho-weather/tests/bootstrap.php .gitignore
git commit -m "feat(weather): scaffold plugin with composer + phpunit"
```

---

## Task 2: Cities config

**Files:**
- Create: `plugins/cafezinho-weather/config/cities.php`

- [ ] **Step 1: Create cities config**

`plugins/cafezinho-weather/config/cities.php`:

```php
<?php
/**
 * Lista das 6 cidades cobertas pelo widget.
 * Ordem aqui = ordem de renderização das abas (esquerda → direita).
 */
return [
    'londres'   => [ 'country' => 'Reino Unido', 'city' => 'Londres',   'flag' => 'gb', 'lat' => 51.5074, 'lon' => -0.1278 ],
    'paris'     => [ 'country' => 'França',      'city' => 'Paris',     'flag' => 'fr', 'lat' => 48.8566, 'lon' => 2.3522 ],
    'berlim'    => [ 'country' => 'Alemanha',    'city' => 'Berlim',    'flag' => 'de', 'lat' => 52.5200, 'lon' => 13.4050 ],
    'madri'     => [ 'country' => 'Espanha',     'city' => 'Madri',     'flag' => 'es', 'lat' => 40.4168, 'lon' => -3.7038 ],
    'roma'      => [ 'country' => 'Itália',      'city' => 'Roma',      'flag' => 'it', 'lat' => 41.9028, 'lon' => 12.4964 ],
    'estocolmo' => [ 'country' => 'Suécia',      'city' => 'Estocolmo', 'flag' => 'se', 'lat' => 59.3293, 'lon' => 18.0686 ],
];
```

- [ ] **Step 2: Commit**

```
git add plugins/cafezinho-weather/config/cities.php
git commit -m "feat(weather): add cities config (6 capitals)"
```

---

## Task 3: WMO code mapping (TDD)

**Files:**
- Create: `plugins/cafezinho-weather/tests/test-wmo-codes.php`
- Create: `plugins/cafezinho-weather/includes/wmo-codes.php`

- [ ] **Step 1: Write failing tests**

`plugins/cafezinho-weather/tests/test-wmo-codes.php`:

```php
<?php
use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../includes/wmo-codes.php';

class WmoCodesTest extends TestCase {

    public function test_sun_code() {
        $r = cafezinho_wmo_lookup( 0 );
        $this->assertSame( 'sun', $r['icon'] );
        $this->assertSame( 'Sol', $r['label'] );
    }

    public function test_partly_cloudy_codes() {
        foreach ( [ 1, 2 ] as $code ) {
            $r = cafezinho_wmo_lookup( $code );
            $this->assertSame( 'sun-cloud', $r['icon'] );
            $this->assertSame( 'Parcialmente nublado', $r['label'] );
        }
    }

    public function test_rain_codes() {
        foreach ( [ 61, 63, 65 ] as $code ) {
            $r = cafezinho_wmo_lookup( $code );
            $this->assertSame( 'rain', $r['icon'] );
            $this->assertSame( 'Chuva', $r['label'] );
        }
    }

    public function test_unknown_code_falls_back() {
        $r = cafezinho_wmo_lookup( 999 );
        $this->assertSame( 'cloud', $r['icon'] );
        $this->assertSame( 'Indefinido', $r['label'] );
    }

    public function test_all_supported_codes_resolve() {
        $codes = [ 0, 1, 2, 3, 45, 48, 51, 53, 55, 61, 63, 65, 71, 73, 75, 80, 81, 82, 95 ];
        foreach ( $codes as $code ) {
            $r = cafezinho_wmo_lookup( $code );
            $this->assertNotSame( 'Indefinido', $r['label'], "Code $code should be mapped" );
        }
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run from `plugins/cafezinho-weather/`:

```
vendor/bin/phpunit --filter WmoCodesTest
```

Expected: FAIL — "wmo-codes.php" file not found (or `cafezinho_wmo_lookup` undefined).

- [ ] **Step 3: Implement wmo-codes.php**

`plugins/cafezinho-weather/includes/wmo-codes.php`:

```php
<?php
/**
 * Mapeia códigos WMO (Open-Meteo) para ícone + descrição em pt-BR.
 * Códigos desconhecidos caem em fallback genérico.
 */

function cafezinho_wmo_table(): array {
    return [
        0  => [ 'icon' => 'sun',          'label' => 'Sol' ],
        1  => [ 'icon' => 'sun-cloud',    'label' => 'Parcialmente nublado' ],
        2  => [ 'icon' => 'sun-cloud',    'label' => 'Parcialmente nublado' ],
        3  => [ 'icon' => 'cloud',        'label' => 'Nublado' ],
        45 => [ 'icon' => 'fog',          'label' => 'Neblina' ],
        48 => [ 'icon' => 'fog',          'label' => 'Neblina' ],
        51 => [ 'icon' => 'drizzle',      'label' => 'Garoa' ],
        53 => [ 'icon' => 'drizzle',      'label' => 'Garoa' ],
        55 => [ 'icon' => 'drizzle',      'label' => 'Garoa' ],
        61 => [ 'icon' => 'rain',         'label' => 'Chuva' ],
        63 => [ 'icon' => 'rain',         'label' => 'Chuva' ],
        65 => [ 'icon' => 'rain',         'label' => 'Chuva' ],
        71 => [ 'icon' => 'snow',         'label' => 'Neve' ],
        73 => [ 'icon' => 'snow',         'label' => 'Neve' ],
        75 => [ 'icon' => 'snow',         'label' => 'Neve' ],
        80 => [ 'icon' => 'shower',       'label' => 'Pancadas' ],
        81 => [ 'icon' => 'shower',       'label' => 'Pancadas' ],
        82 => [ 'icon' => 'shower',       'label' => 'Pancadas' ],
        95 => [ 'icon' => 'thunderstorm', 'label' => 'Trovoada' ],
    ];
}

function cafezinho_wmo_lookup( int $code ): array {
    $table = cafezinho_wmo_table();
    return $table[ $code ] ?? [ 'icon' => 'cloud', 'label' => 'Indefinido' ];
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```
vendor/bin/phpunit --filter WmoCodesTest
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```
git add plugins/cafezinho-weather/tests/test-wmo-codes.php plugins/cafezinho-weather/includes/wmo-codes.php
git commit -m "feat(weather): WMO code → icon + pt-BR label mapping"
```

---

## Task 4: Open-Meteo response fixture

**Files:**
- Create: `plugins/cafezinho-weather/tests/fixtures/open-meteo-paris.json`

- [ ] **Step 1: Capture a real Open-Meteo response**

Run (any shell):

```
curl "https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto&forecast_days=3" > plugins/cafezinho-weather/tests/fixtures/open-meteo-paris.json
```

Expected: file ~500 bytes, contains `"daily"` with three dates.

- [ ] **Step 2: Sanity-check the fixture**

Open the file. Confirm it contains:
- `daily.time` → array of 3 ISO dates
- `daily.temperature_2m_max` → array of 3 floats
- `daily.temperature_2m_min` → array of 3 floats
- `daily.weather_code` → array of 3 integers

If any are missing, re-run the curl (the API can occasionally return partial data; not normal but harmless to retry).

- [ ] **Step 3: Commit**

```
git add plugins/cafezinho-weather/tests/fixtures/open-meteo-paris.json
git commit -m "test(weather): add Open-Meteo Paris fixture"
```

---

## Task 5: Weather_Fetcher::parse_response (TDD)

**Files:**
- Create: `plugins/cafezinho-weather/tests/test-weather-fetcher.php`
- Create: `plugins/cafezinho-weather/includes/class-weather-fetcher.php`

- [ ] **Step 1: Write failing tests**

`plugins/cafezinho-weather/tests/test-weather-fetcher.php`:

```php
<?php
use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../includes/class-weather-fetcher.php';

class WeatherFetcherParseTest extends TestCase {

    private function load_fixture(): array {
        $raw = file_get_contents( __DIR__ . '/fixtures/open-meteo-paris.json' );
        return json_decode( $raw, true );
    }

    public function test_parse_valid_response_returns_3_days() {
        $days = Cafezinho_Weather_Fetcher::parse_response( $this->load_fixture() );
        $this->assertCount( 3, $days );
    }

    public function test_parse_returns_normalized_keys() {
        $days = Cafezinho_Weather_Fetcher::parse_response( $this->load_fixture() );
        $this->assertArrayHasKey( 'date', $days[0] );
        $this->assertArrayHasKey( 'max',  $days[0] );
        $this->assertArrayHasKey( 'min',  $days[0] );
        $this->assertArrayHasKey( 'code', $days[0] );
    }

    public function test_parse_temperatures_are_rounded_integers() {
        $days = Cafezinho_Weather_Fetcher::parse_response( $this->load_fixture() );
        foreach ( $days as $d ) {
            $this->assertIsInt( $d['max'] );
            $this->assertIsInt( $d['min'] );
            $this->assertIsInt( $d['code'] );
            $this->assertIsString( $d['date'] );
        }
    }

    public function test_parse_throws_on_missing_daily_key() {
        $this->expectException( RuntimeException::class );
        Cafezinho_Weather_Fetcher::parse_response( [ 'foo' => 'bar' ] );
    }

    public function test_parse_throws_on_array_length_mismatch() {
        $bad = [
            'daily' => [
                'time'               => [ '2026-06-07', '2026-06-08' ],   // 2 dates
                'temperature_2m_max' => [ 18.0, 19.0, 17.0 ],             // 3 values
                'temperature_2m_min' => [ 11.0, 12.0, 10.0 ],
                'weather_code'       => [ 3, 61, 80 ],
            ],
        ];
        $this->expectException( RuntimeException::class );
        Cafezinho_Weather_Fetcher::parse_response( $bad );
    }

    public function test_parse_throws_on_non_numeric_temperature() {
        $bad = [
            'daily' => [
                'time'               => [ '2026-06-07' ],
                'temperature_2m_max' => [ 'hot' ],
                'temperature_2m_min' => [ 11.0 ],
                'weather_code'       => [ 3 ],
            ],
        ];
        $this->expectException( RuntimeException::class );
        Cafezinho_Weather_Fetcher::parse_response( $bad );
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```
vendor/bin/phpunit --filter WeatherFetcherParseTest
```

Expected: FAIL — class `Cafezinho_Weather_Fetcher` not found.

- [ ] **Step 3: Implement parse_response**

`plugins/cafezinho-weather/includes/class-weather-fetcher.php`:

```php
<?php
/**
 * Cliente Open-Meteo para o widget de previsão.
 */
class Cafezinho_Weather_Fetcher {

    private const ENDPOINT = 'https://api.open-meteo.com/v1/forecast';
    private const TIMEOUT  = 5;
    private const DAYS     = 3;

    /**
     * Valida e normaliza a resposta crua da Open-Meteo.
     *
     * @return array<int, array{date:string,max:int,min:int,code:int}>
     * @throws RuntimeException se a resposta estiver malformada.
     */
    public static function parse_response( array $raw ): array {
        if ( ! isset( $raw['daily'] ) || ! is_array( $raw['daily'] ) ) {
            throw new RuntimeException( 'Open-Meteo response missing "daily" key' );
        }
        $d = $raw['daily'];
        foreach ( [ 'time', 'temperature_2m_max', 'temperature_2m_min', 'weather_code' ] as $k ) {
            if ( ! isset( $d[ $k ] ) || ! is_array( $d[ $k ] ) ) {
                throw new RuntimeException( "Open-Meteo response missing array key: $k" );
            }
        }
        $n = count( $d['time'] );
        if ( $n < self::DAYS ) {
            throw new RuntimeException( "Open-Meteo response has only $n days; expected " . self::DAYS );
        }
        foreach ( [ 'temperature_2m_max', 'temperature_2m_min', 'weather_code' ] as $k ) {
            if ( count( $d[ $k ] ) !== $n ) {
                throw new RuntimeException( "Open-Meteo response array length mismatch on: $k" );
            }
        }

        $days = [];
        for ( $i = 0; $i < self::DAYS; $i++ ) {
            if ( ! is_numeric( $d['temperature_2m_max'][ $i ] ) ||
                 ! is_numeric( $d['temperature_2m_min'][ $i ] ) ||
                 ! is_numeric( $d['weather_code'][ $i ] ) ) {
                throw new RuntimeException( "Open-Meteo response non-numeric value at index $i" );
            }
            $days[] = [
                'date' => (string) $d['time'][ $i ],
                'max'  => (int) round( $d['temperature_2m_max'][ $i ] ),
                'min'  => (int) round( $d['temperature_2m_min'][ $i ] ),
                'code' => (int) $d['weather_code'][ $i ],
            ];
        }
        return $days;
    }

    public static function build_url( float $lat, float $lon ): string {
        return self::ENDPOINT . '?' . http_build_query( [
            'latitude'      => $lat,
            'longitude'     => $lon,
            'daily'         => 'temperature_2m_max,temperature_2m_min,weather_code',
            'timezone'      => 'auto',
            'forecast_days' => self::DAYS,
        ] );
    }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```
vendor/bin/phpunit --filter WeatherFetcherParseTest
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```
git add plugins/cafezinho-weather/tests/test-weather-fetcher.php plugins/cafezinho-weather/includes/class-weather-fetcher.php
git commit -m "feat(weather): Weather_Fetcher::parse_response with strict validation"
```

---

## Task 6: Weather_Fetcher::fetch_all (parallel HTTP)

**Files:**
- Modify: `plugins/cafezinho-weather/includes/class-weather-fetcher.php`

`fetch_all` uses `Requests::request_multiple` (bundled with WordPress) — it can't run in pure-PHP unit tests without WP loaded. It will be exercised by the smoke script in Task 9 instead.

- [ ] **Step 1: Add fetch_all method**

Append to `plugins/cafezinho-weather/includes/class-weather-fetcher.php` (before the closing `}`):

```php
    /**
     * Busca dados de todas as cidades em paralelo.
     * Cidades que falharem ficam ausentes do array devolvido (merge cuida do fallback).
     *
     * @param array<string, array{country:string,city:string,flag:string,lat:float,lon:float}> $cities
     * @return array<string, array{country:string,city:string,flag:string,fetched_at:int,days:array}>
     */
    public static function fetch_all( array $cities ): array {
        if ( ! class_exists( 'WpOrg\\Requests\\Requests' ) && ! class_exists( 'Requests' ) ) {
            throw new RuntimeException( 'WordPress Requests library not available' );
        }
        $requests_class = class_exists( 'WpOrg\\Requests\\Requests' ) ? 'WpOrg\\Requests\\Requests' : 'Requests';

        $requests = [];
        foreach ( $cities as $slug => $cfg ) {
            $requests[ $slug ] = [
                'url'     => self::build_url( $cfg['lat'], $cfg['lon'] ),
                'type'    => $requests_class::GET,
                'options' => [ 'timeout' => self::TIMEOUT ],
            ];
        }

        $responses = $requests_class::request_multiple( $requests );
        $now       = time();
        $out       = [];

        foreach ( $responses as $slug => $resp ) {
            $cfg = $cities[ $slug ];
            try {
                if ( $resp instanceof \Exception || $resp instanceof \Throwable ) {
                    throw new RuntimeException( 'HTTP error: ' . $resp->getMessage() );
                }
                if ( $resp->status_code !== 200 ) {
                    throw new RuntimeException( "HTTP {$resp->status_code} for {$cfg['city']}" );
                }
                $raw  = json_decode( $resp->body, true );
                if ( ! is_array( $raw ) ) {
                    throw new RuntimeException( "Invalid JSON for {$cfg['city']}" );
                }
                $days = self::parse_response( $raw );
                $out[ $slug ] = [
                    'country'    => $cfg['country'],
                    'city'       => $cfg['city'],
                    'flag'       => $cfg['flag'],
                    'fetched_at' => $now,
                    'days'       => $days,
                ];
            } catch ( Throwable $e ) {
                error_log( '[cafezinho-weather] fetch failed for ' . $slug . ': ' . $e->getMessage() );
            }
        }
        return $out;
    }
```

- [ ] **Step 2: Re-run all tests to confirm nothing broke**

Run:

```
vendor/bin/phpunit
```

Expected: all previous tests pass.

- [ ] **Step 3: Commit**

```
git add plugins/cafezinho-weather/includes/class-weather-fetcher.php
git commit -m "feat(weather): fetch_all uses parallel HTTP via WP Requests"
```

---

## Task 7: Weather_Cache (TDD)

**Files:**
- Create: `plugins/cafezinho-weather/tests/test-weather-cache.php`
- Create: `plugins/cafezinho-weather/includes/class-weather-cache.php`

- [ ] **Step 1: Write failing tests**

`plugins/cafezinho-weather/tests/test-weather-cache.php`:

```php
<?php
use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../includes/class-weather-cache.php';

class WeatherCacheTest extends TestCase {

    protected function setUp(): void {
        $GLOBALS['__cw_transients'] = [];
    }

    private function city( string $slug, int $max ): array {
        return [
            'country'    => 'X',
            'city'       => ucfirst( $slug ),
            'flag'       => 'xx',
            'fetched_at' => 1000,
            'days'       => [
                [ 'date' => '2026-06-07', 'max' => $max, 'min' => 10, 'code' => 3 ],
                [ 'date' => '2026-06-08', 'max' => $max, 'min' => 10, 'code' => 3 ],
                [ 'date' => '2026-06-09', 'max' => $max, 'min' => 10, 'code' => 3 ],
            ],
        ];
    }

    public function test_get_returns_null_when_empty() {
        $this->assertNull( Cafezinho_Weather_Cache::get() );
    }

    public function test_merge_and_store_full_fresh_data() {
        $fresh = [
            'paris'    => $this->city( 'paris', 18 ),
            'londres'  => $this->city( 'londres', 14 ),
        ];
        Cafezinho_Weather_Cache::merge_and_store( $fresh );
        $cached = Cafezinho_Weather_Cache::get();
        $this->assertCount( 2, $cached['cities'] );
        $this->assertSame( 18, $cached['cities']['paris']['days'][0]['max'] );
        $this->assertArrayHasKey( 'updated_at', $cached );
    }

    public function test_merge_preserves_missing_city_from_previous_cache() {
        Cafezinho_Weather_Cache::merge_and_store( [
            'paris'   => $this->city( 'paris', 18 ),
            'londres' => $this->city( 'londres', 14 ),
        ] );
        // Second refresh: only paris came back; londres failed.
        Cafezinho_Weather_Cache::merge_and_store( [
            'paris' => $this->city( 'paris', 20 ),
        ] );
        $cached = Cafezinho_Weather_Cache::get();
        $this->assertSame( 20, $cached['cities']['paris']['days'][0]['max'] );
        $this->assertSame( 14, $cached['cities']['londres']['days'][0]['max'], 'londres should keep old reading' );
    }

    public function test_merge_with_empty_fresh_does_not_wipe_cache() {
        Cafezinho_Weather_Cache::merge_and_store( [
            'paris' => $this->city( 'paris', 18 ),
        ] );
        Cafezinho_Weather_Cache::merge_and_store( [] );
        $cached = Cafezinho_Weather_Cache::get();
        $this->assertSame( 18, $cached['cities']['paris']['days'][0]['max'] );
    }

    public function test_clear_removes_cache() {
        Cafezinho_Weather_Cache::merge_and_store( [
            'paris' => $this->city( 'paris', 18 ),
        ] );
        Cafezinho_Weather_Cache::clear();
        $this->assertNull( Cafezinho_Weather_Cache::get() );
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```
vendor/bin/phpunit --filter WeatherCacheTest
```

Expected: FAIL — class `Cafezinho_Weather_Cache` not found.

- [ ] **Step 3: Implement Weather_Cache**

`plugins/cafezinho-weather/includes/class-weather-cache.php`:

```php
<?php
/**
 * Gerencia o transient `cafezinho_weather` com merge gracioso por cidade.
 */
class Cafezinho_Weather_Cache {

    public  const TRANSIENT_KEY = 'cafezinho_weather';
    public  const TTL_SECONDS   = 3 * HOUR_IN_SECONDS_FALLBACK;

    public static function get(): ?array {
        $v = get_transient( self::TRANSIENT_KEY );
        return ( is_array( $v ) && isset( $v['cities'] ) ) ? $v : null;
    }

    /**
     * Mescla `$fresh` com o cache existente. Cidades ausentes em `$fresh` mantêm
     * a leitura anterior.
     */
    public static function merge_and_store( array $fresh ): void {
        $existing = self::get() ?? [ 'cities' => [] ];
        $merged   = $existing['cities'];

        foreach ( $fresh as $slug => $city ) {
            $merged[ $slug ] = $city;
        }

        // If nothing fresh AND nothing existing, don't write garbage.
        if ( empty( $merged ) ) {
            return;
        }

        $payload = [
            'updated_at' => time(),
            'cities'     => $merged,
        ];
        set_transient( self::TRANSIENT_KEY, $payload, self::TTL_SECONDS );
    }

    public static function clear(): void {
        delete_transient( self::TRANSIENT_KEY );
    }
}

if ( ! defined( 'HOUR_IN_SECONDS_FALLBACK' ) ) {
    // WP defines HOUR_IN_SECONDS = 3600; tests run without WP loaded, so we
    // provide a constant the class uses regardless of environment.
    define( 'HOUR_IN_SECONDS_FALLBACK', defined( 'HOUR_IN_SECONDS' ) ? HOUR_IN_SECONDS : 3600 );
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```
vendor/bin/phpunit --filter WeatherCacheTest
```

Expected: 5 tests pass.

- [ ] **Step 5: Run full test suite**

Run:

```
vendor/bin/phpunit
```

Expected: all tests (WMO + Fetcher parse + Cache) pass.

- [ ] **Step 6: Commit**

```
git add plugins/cafezinho-weather/tests/test-weather-cache.php plugins/cafezinho-weather/includes/class-weather-cache.php
git commit -m "feat(weather): Weather_Cache with per-city graceful merge"
```

---

## Task 8: Weather_Cron (handler + schedule)

**Files:**
- Create: `plugins/cafezinho-weather/includes/class-weather-cron.php`

No unit tests for this class — registration with WP-Cron is integration territory and is exercised by the smoke test in Task 9 and the live verification in Task 13.

- [ ] **Step 1: Implement Weather_Cron**

`plugins/cafezinho-weather/includes/class-weather-cron.php`:

```php
<?php
/**
 * Registra evento WP-Cron a cada 2h e dispara o refresh.
 */
class Cafezinho_Weather_Cron {

    public const HOOK          = 'cafezinho_weather_refresh';
    public const SCHEDULE      = 'cafezinho_2h';
    public const LOCK_KEY      = 'cafezinho_weather_lock';
    public const LOCK_TTL      = 60;
    public const FAILURE_KEY   = 'cafezinho_weather_consecutive_failures';

    public static function register_schedule( array $schedules ): array {
        $schedules[ self::SCHEDULE ] = [
            'interval' => 2 * HOUR_IN_SECONDS,
            'display'  => 'A cada 2 horas (Cafezinho Weather)',
        ];
        return $schedules;
    }

    public static function on_activate(): void {
        if ( ! wp_next_scheduled( self::HOOK ) ) {
            wp_schedule_event( time() + 30, self::SCHEDULE, self::HOOK );
        }
    }

    public static function on_deactivate(): void {
        wp_clear_scheduled_hook( self::HOOK );
        delete_transient( self::LOCK_KEY );
    }

    /**
     * Handler do hook. Pega o lock, busca os 6 países e mescla.
     */
    public static function handle_refresh(): void {
        if ( get_transient( self::LOCK_KEY ) ) {
            return; // Outra execução em andamento.
        }
        set_transient( self::LOCK_KEY, 1, self::LOCK_TTL );

        try {
            $cities = require CAFEZINHO_WEATHER_PATH . 'config/cities.php';
            $fresh  = Cafezinho_Weather_Fetcher::fetch_all( $cities );
            Cafezinho_Weather_Cache::merge_and_store( $fresh );

            $expected = count( $cities );
            $got      = count( $fresh );
            if ( $got === 0 ) {
                update_option( self::FAILURE_KEY, (int) get_option( self::FAILURE_KEY, 0 ) + 1 );
                error_log( '[cafezinho-weather] refresh: all cities failed' );
            } else {
                update_option( self::FAILURE_KEY, 0 );
                error_log( "[cafezinho-weather] refresh: $got/$expected cities OK" );
            }
        } catch ( Throwable $e ) {
            error_log( '[cafezinho-weather] refresh exception: ' . $e->getMessage() );
        } finally {
            delete_transient( self::LOCK_KEY );
        }
    }
}
```

- [ ] **Step 2: Verify file parses (no syntax errors)**

Run from `plugins/cafezinho-weather/`:

```
php -l includes/class-weather-cron.php
```

Expected: `No syntax errors detected`.

- [ ] **Step 3: Commit**

```
git add plugins/cafezinho-weather/includes/class-weather-cron.php
git commit -m "feat(weather): Weather_Cron schedule + refresh handler with lock"
```

---

## Task 9: Smoke test CLI script

**Files:**
- Create: `plugins/cafezinho-weather/bin/smoke-weather.php`

- [ ] **Step 1: Implement smoke script**

`plugins/cafezinho-weather/bin/smoke-weather.php`:

```php
<?php
/**
 * Smoke test: chama Open-Meteo de verdade para todas as 6 cidades e
 * valida que `parse_response` aceita cada uma.
 *
 * Uso:  php bin/smoke-weather.php
 * Saída: linha por cidade com hoje/amanhã/depois ou ERRO.
 * Não escreve em cache, não toca em WordPress.
 */

require_once __DIR__ . '/../includes/class-weather-fetcher.php';

$cities  = require __DIR__ . '/../config/cities.php';
$ok      = 0;
$failed  = 0;

foreach ( $cities as $slug => $cfg ) {
    $url = Cafezinho_Weather_Fetcher::build_url( $cfg['lat'], $cfg['lon'] );

    $ctx = stream_context_create( [ 'http' => [ 'timeout' => 5 ] ] );
    $body = @file_get_contents( $url, false, $ctx );
    if ( $body === false ) {
        echo str_pad( $cfg['city'], 12 ) . "  ERRO HTTP\n";
        $failed++;
        continue;
    }
    try {
        $days = Cafezinho_Weather_Fetcher::parse_response( json_decode( $body, true ) );
        printf(
            "%s  hoje %d/%d  amanhã %d/%d  depois %d/%d  (códigos %d/%d/%d)\n",
            str_pad( $cfg['city'], 12 ),
            $days[0]['max'], $days[0]['min'],
            $days[1]['max'], $days[1]['min'],
            $days[2]['max'], $days[2]['min'],
            $days[0]['code'], $days[1]['code'], $days[2]['code']
        );
        $ok++;
    } catch ( Throwable $e ) {
        echo str_pad( $cfg['city'], 12 ) . "  ERRO parse: " . $e->getMessage() . "\n";
        $failed++;
    }
}

echo "\nResumo: $ok ok, $failed falhas\n";
exit( $failed === 0 ? 0 : 1 );
```

- [ ] **Step 2: Run the smoke script**

Run from `plugins/cafezinho-weather/`:

```
php bin/smoke-weather.php
```

Expected: 6 lines, one per city, all showing temperatures. Exit code 0.

If any city errors, investigate — likely a temporary Open-Meteo blip. Re-run once.

- [ ] **Step 3: Commit**

```
git add plugins/cafezinho-weather/bin/smoke-weather.php
git commit -m "test(weather): smoke script hits real Open-Meteo for 6 cities"
```

---

## Task 10: WMO description map (for textual weather labels)

**Files:**
- Modify: `plugins/cafezinho-weather/includes/wmo-codes.php`
- Modify: `plugins/cafezinho-weather/tests/test-wmo-codes.php`

The visual direction (see spec §8) shows a short italic textual description next to each day's icon ("Sol entre nuvens, brisa fraca"). The existing WMO map only has icon + label; we now reuse the same `label` field as the description, but cross-check that the labels read well as italic sentence fragments.

- [ ] **Step 1: Verify existing labels work as italic sentences**

Open `plugins/cafezinho-weather/includes/wmo-codes.php` and review the `label` strings. They already read as short descriptive fragments (`Sol`, `Parcialmente nublado`, `Garoa`, `Chuva`, `Neve`, `Pancadas`, `Trovoada`, `Neblina`, `Indefinido`).

No code change needed — confirmed compatible with the editorial visual direction.

- [ ] **Step 2: Mark Task 10 as a no-op in commit log (so the task numbers stay stable across the plan)**

```
git commit --allow-empty -m "docs(weather): confirm WMO labels double as italic descriptions"
```

---

## Task 11: Weather_Widget (render HTML — editorial banner style)

**Files:**
- Create: `plugins/cafezinho-weather/includes/class-weather-widget.php`

The HTML structure must mirror the validated mockup at `design/weather-bar.html` so the CSS in Task 12 applies cleanly. Key differences from earlier draft: no separate `.cw-bar` wrapper, no per-city visible panels in markup (a single panel slot starts hidden and is populated by JS from data attributes on the buttons).

- [ ] **Step 1: Implement Weather_Widget**

`plugins/cafezinho-weather/includes/class-weather-widget.php`:

```php
<?php
/**
 * Renderiza o strip de tempo dentro do banner editorial.
 * Função pública: cafezinho_render_weather_bar()
 */
class Cafezinho_Weather_Widget {

    public const DEFAULT_CITY = 'paris';

    public static function render(): void {
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
        // Map our flag slugs to ISO display codes (uppercased).
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
```

- [ ] **Step 2: Syntax check**

Run from `plugins/cafezinho-weather/`:

```
php -l includes/class-weather-widget.php
```

Expected: `No syntax errors detected`.

- [ ] **Step 3: Commit**

```
git add plugins/cafezinho-weather/includes/class-weather-widget.php
git commit -m "feat(weather): Weather_Widget renders editorial banner strip + lazy panel"
```

---

## Task 12: CSS + JS (editorial visual)

**Files:**
- Create: `plugins/cafezinho-weather/assets/weather.css`
- Create: `plugins/cafezinho-weather/assets/weather.js`

Both files mirror the validated mockup at `design/weather-bar.html`. The CSS assumes the host theme defines the design tokens (`--bg`, `--ink`, `--caramelo-deep`, etc.) — the plugin **also** falls back to literal values so it renders correctly on any theme (including the WP default during development).

- [ ] **Step 1: Create weather.css**

`plugins/cafezinho-weather/assets/weather.css`:

```css
/* ============================================================
   Cafezinho Weather widget — editorial visual
   Mirrors design/weather-bar.html. Token fallbacks let the
   widget render correctly even when host theme does not
   define the design system custom properties.
   ============================================================ */

.cw {
    --cw-bg:            var(--bg, #FAF6F0);
    --cw-ink:           var(--ink, #2A1812);
    --cw-ink-soft:      var(--ink-soft, #5A3F35);
    --cw-ink-light:     var(--ink-light, #8C6F62);
    --cw-line:          var(--line, #D7C8B8);
    --cw-line-soft:     var(--line-soft, #E3D5C2);
    --cw-caramelo-deep: var(--caramelo-deep, #8C4F12);
    --cw-crema:         var(--crema, #EBD9C2);

    position: relative;
    display: inline-flex;
    flex-direction: column;
    align-items: flex-end;
    justify-self: end;
    text-align: right;
    color: var(--cw-ink-soft);
    font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.cw__strip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.cw__supra {
    margin-right: 14px;
    color: var(--cw-ink-light);
    font-size: 10px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    position: relative;
    padding-right: 14px;
}
.cw__supra::after {
    content: '';
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 1px;
    height: 11px;
    background: var(--cw-line);
}
.cw__supra--solo { padding-right: 0; }
.cw__supra--solo::after { display: none; }

.cw__tab {
    appearance: none;
    background: transparent;
    border: none;
    padding: 4px 2px 6px;
    margin: 0;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: inherit;
    font-size: 11px;
    color: var(--cw-ink-soft);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    position: relative;
    transition: color 0.18s ease;
    border-radius: 0;
}
.cw__tab + .cw__tab { margin-left: 4px; }
.cw__tab:hover { color: var(--cw-ink); }
.cw__tab .flag {
    width: 18px;
    height: 12px;
    display: inline-block;
    border: 0.5px solid var(--cw-ink-light);
    border-radius: 1px;
    transition: transform 0.18s ease;
}
.cw__tab:hover .flag { transform: translateY(-1px); }
.cw__tab .cw__temp {
    font-weight: 500;
    font-variant-numeric: tabular-nums;
    color: var(--cw-ink);
}
.cw__tab.is-active { color: var(--cw-caramelo-deep); }
.cw__tab.is-active .cw__temp { color: var(--cw-caramelo-deep); }
.cw__tab.is-active::after {
    content: '';
    position: absolute;
    left: 50%;
    bottom: -3px;
    width: 6px;
    height: 6px;
    background: var(--cw-caramelo-deep);
    border-radius: 50%;
    transform: translateX(-50%);
}

/* ─── Flag gradients (same convention as design/home.html) ─── */
.cw .flag.uk,
.cw .flag.gb { background: #012169; position: relative; overflow: hidden; }
.cw .flag.uk::before,
.cw .flag.gb::before {
    content: '';
    position: absolute;
    inset: 0;
    background:
        linear-gradient(45deg,  transparent 45%, #fff 45% 55%, transparent 55%),
        linear-gradient(-45deg, transparent 45%, #fff 45% 55%, transparent 55%);
}
.cw .flag.uk::after,
.cw .flag.gb::after {
    content: '';
    position: absolute;
    inset: 0;
    background:
        linear-gradient(90deg, transparent 42%, #C8102E 42% 58%, transparent 58%),
        linear-gradient(0deg,  transparent 42%, #C8102E 42% 58%, transparent 58%);
}
.cw .flag.fr { background: linear-gradient(to right,  #002395 33%, #fff 33% 66%, #ED2939 66%); }
.cw .flag.de { background: linear-gradient(to bottom, #000    33%, #DD0000 33% 66%, #FFCE00 66%); }
.cw .flag.es { background: linear-gradient(to bottom, #C60B1E 25%, #FFC400 25% 75%, #C60B1E 75%); }
.cw .flag.it { background: linear-gradient(to right,  #008C45 33%, #fff 33% 66%, #CD212A 66%); }
.cw .flag.se {
    background: linear-gradient(to bottom, #006AA7 40%, #FECC00 40% 60%, #006AA7 60%);
    position: relative;
}
.cw .flag.se::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(to right, transparent 30%, #FECC00 30% 42%, transparent 42%);
}

/* ─── Dropdown panel ─── */
.cw__panel {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    min-width: 360px;
    background: var(--cw-bg);
    border: 1px solid var(--cw-ink);
    padding: 22px 26px 20px;
    text-align: left;
    z-index: 50;
    transform-origin: top right;
    opacity: 0;
    transform: translateY(-6px) scale(0.985);
    pointer-events: none;
    transition: opacity 0.2s ease, transform 0.22s cubic-bezier(0.16,1,0.3,1);
    box-shadow:
        0 1px 0 var(--cw-ink),
        14px 14px 0 -10px var(--cw-crema),
        16px 16px 0 -10px var(--cw-ink);
}
.cw__panel[data-open="true"] {
    opacity: 1;
    transform: translateY(0) scale(1);
    pointer-events: auto;
}
.cw__panel::before {
    content: '';
    position: absolute;
    top: -7px;
    right: 24px;
    width: 12px;
    height: 12px;
    background: var(--cw-bg);
    border-left: 1px solid var(--cw-ink);
    border-top:  1px solid var(--cw-ink);
    transform: rotate(45deg);
}

.cw__panel-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 16px;
    padding-bottom: 10px;
    border-bottom: 1px dashed var(--cw-line);
    margin-bottom: 16px;
}
.cw__panel-city {
    font-family: 'Fraunces', Georgia, serif;
    font-style: italic;
    font-weight: 600;
    font-variation-settings: "SOFT" 100, "WONK" 1;
    font-size: 28px;
    line-height: 1;
    color: var(--cw-ink);
    letter-spacing: -0.01em;
}
.cw__panel-city em {
    font-style: normal;
    color: var(--cw-caramelo-deep);
    margin-right: 6px;
    letter-spacing: 0;
}
.cw__panel-meta {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    color: var(--cw-ink-light);
}

.cw__days {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
}
.cw__day {
    display: flex;
    flex-direction: column;
    gap: 6px;
    position: relative;
}
.cw__day + .cw__day::before {
    content: '';
    position: absolute;
    left: -9px;
    top: 4px;
    bottom: 4px;
    width: 1px;
    background: var(--cw-line-soft);
}
.cw__day-label {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    color: var(--cw-ink-light);
}
.cw__day-temps {
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 500;
    font-variation-settings: "SOFT" 50, "WONK" 0;
    font-size: 26px;
    line-height: 1;
    color: var(--cw-ink);
    font-variant-numeric: tabular-nums;
    display: flex;
    align-items: baseline;
    gap: 6px;
}
.cw__day-temps .min  { font-size: 14px; color: var(--cw-ink-light); font-weight: 400; }
.cw__day-temps .deg  { font-size: 16px; vertical-align: top; color: var(--cw-caramelo-deep); }
.cw__day-desc {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'Newsreader', Georgia, serif;
    font-style: italic;
    font-size: 12px;
    color: var(--cw-ink-soft);
    margin-top: 2px;
}
.cw__day-icon {
    display: inline-block;
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    color: var(--cw-caramelo-deep);
}

.cw__panel-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px dashed var(--cw-line);
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    color: var(--cw-ink-light);
}
.cw__panel-foot a {
    color: var(--cw-caramelo-deep);
    text-decoration: none;
    border-bottom: 1px solid currentColor;
    padding-bottom: 1px;
}

/* ─── Placeholder while cache is cold ─── */
.cw--placeholder { font-style: italic; }

/* ─── Mobile ─── */
@media (max-width: 768px) {
    .cw { align-items: center; justify-self: center; text-align: center; }
    .cw__supra { display: none; }
    .cw__strip { flex-wrap: wrap; justify-content: center; gap: 2px 8px; }
    .cw__panel {
        right: 50%;
        transform: translateX(50%) translateY(-6px) scale(0.985);
        min-width: min(92vw, 360px);
    }
    .cw__panel[data-open="true"] {
        transform: translateX(50%) translateY(0) scale(1);
    }
    .cw__panel::before {
        right: auto;
        left: 50%;
        transform: translateX(-50%) rotate(45deg);
    }
}
```

- [ ] **Step 2: Create weather.js**

`plugins/cafezinho-weather/assets/weather.js`:

```javascript
(function () {
    'use strict';

    var ICONS = {
        sun:        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4l1.4-1.4M17 7l1.4-1.4"/></svg>',
        'sun-cloud':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="10" r="3"/><path d="M9 6V4M9 14v2M5 10H3M15 10h-2M6.5 6.5L5 5M11.5 6.5L13 5M6.5 13.5L5 15"/><path d="M10 18a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0122 18z"/></svg>',
        cloud:      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 17a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 17z"/></svg>',
        fog:        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><line x1="3" y1="8"  x2="21" y2="8"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="16" x2="21" y2="16"/></svg>',
        drizzle:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 14z"/><path d="M9 17v2M13 17v2M17 17v2"/></svg>',
        rain:       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 14z"/><path d="M8 17l-1 4M12 17l-1 4M16 17l-1 4"/></svg>',
        shower:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 15a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 15z"/><path d="M9 18l-1 3M13 18l-1 3M17 18l-1 3"/></svg>',
        snow:       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 14z"/><circle cx="8" cy="19" r="0.8"/><circle cx="12" cy="20" r="0.8"/><circle cx="16" cy="19" r="0.8"/></svg>',
        thunder:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 14z"/><path d="M11 15l-2 4h3l-1 4 4-6h-3l1-3z"/></svg>',
        thunderstorm:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 14z"/><path d="M11 15l-2 4h3l-1 4 4-6h-3l1-3z"/></svg>'
    };

    function esc(s) {
        return String(s).replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    }

    function renderPanel(panel, payload) {
        var daysHtml = payload.days.map(function (d) {
            var icon = ICONS[d.icon] || ICONS.cloud;
            return '<div class="cw__day">' +
                       '<div class="cw__day-label">' + esc(d.label) + '</div>' +
                       '<div class="cw__day-temps">' + d.max + '<span class="deg">°</span><span class="min">' + d.min + '°</span></div>' +
                       '<div class="cw__day-desc">' + icon + ' ' + esc(d.desc) + '</div>' +
                   '</div>';
        }).join('');
        panel.innerHTML =
            '<div class="cw__panel-head">' +
                '<div class="cw__panel-city"><em>' + esc(payload.country) + '</em>' + esc(payload.city) + '</div>' +
                '<div class="cw__panel-meta">' + esc(payload.updated) + '</div>' +
            '</div>' +
            '<div class="cw__days">' + daysHtml + '</div>' +
            '<div class="cw__panel-foot">' +
                '<span>Fonte · Open-Meteo</span>' +
            '</div>';
        // Tag the inline icon SVGs so the CSS sizes them.
        var svgs = panel.querySelectorAll('svg');
        for (var i = 0; i < svgs.length; i++) {
            svgs[i].classList.add('cw__day-icon');
        }
    }

    function setActive(widget, slug) {
        var tabs = widget.querySelectorAll('.cw__tab');
        for (var i = 0; i < tabs.length; i++) {
            var on = tabs[i].dataset.slug === slug;
            tabs[i].classList.toggle('is-active', on);
            tabs[i].setAttribute('aria-selected', on ? 'true' : 'false');
        }
    }

    function clearActive(widget) {
        var tabs = widget.querySelectorAll('.cw__tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].classList.remove('is-active');
            tabs[i].setAttribute('aria-selected', 'false');
        }
    }

    function init(widget) {
        var panel = widget.querySelector('.cw__panel');
        if (!panel) return;
        var currentSlug = null;

        widget.addEventListener('click', function (e) {
            var btn = e.target.closest('.cw__tab');
            if (!btn || !widget.contains(btn)) return;
            var slug = btn.dataset.slug;
            var payloadRaw = btn.dataset.payload;

            if (slug === currentSlug && panel.dataset.open === 'true') {
                panel.dataset.open = 'false';
                clearActive(widget);
                currentSlug = null;
                return;
            }
            try {
                var payload = JSON.parse(payloadRaw);
                renderPanel(panel, payload);
                panel.dataset.open = 'true';
                setActive(widget, slug);
                currentSlug = slug;
            } catch (err) {
                // Bad payload: fail silently, leave panel closed.
                panel.dataset.open = 'false';
            }
        });

        document.addEventListener('click', function (e) {
            if (!widget.contains(e.target) && panel.dataset.open === 'true') {
                panel.dataset.open = 'false';
                clearActive(widget);
                currentSlug = null;
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && panel.dataset.open === 'true') {
                panel.dataset.open = 'false';
                clearActive(widget);
                currentSlug = null;
            }
        });
    }

    function boot() {
        var widgets = document.querySelectorAll('.cw');
        for (var i = 0; i < widgets.length; i++) {
            init(widgets[i]);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
```

- [ ] **Step 3: Commit**

```
git add plugins/cafezinho-weather/assets/weather.css plugins/cafezinho-weather/assets/weather.js
git commit -m "feat(weather): CSS + JS for tab bar (vanilla, no deps)"
```

---

## Task 13: Plugin bootstrap (hooks, assets, fallback banner injection)

**Files:**
- Modify: `plugins/cafezinho-weather/cafezinho-weather.php`

Integration model: the plugin exposes the public function `cafezinho_render_weather_bar()` for the custom theme (Phase 2) to call **from inside its own banner div**. While that custom theme does not exist (default WP theme during development), the plugin auto-injects a complete editorial banner via `wp_body_open` so the widget can be tested visually. The auto-injection is disabled by the theme via the `cafezinho_weather_auto_banner` filter or by defining `CAFEZINHO_WEATHER_NO_AUTO`.

- [ ] **Step 1: Wire up the bootstrap file**

Replace the contents of `plugins/cafezinho-weather/cafezinho-weather.php` with:

```php
<?php
/**
 * Plugin Name: Cafezinho Weather
 * Description: Widget editorial de previsão do tempo para os 6 países cobertos pelo Cafezinho Europa.
 * Version:     0.1.0
 * Author:      Cafezinho Europa
 * License:     MIT
 * Requires PHP: 8.1
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

define( 'CAFEZINHO_WEATHER_VERSION', '0.1.0' );
define( 'CAFEZINHO_WEATHER_PATH', plugin_dir_path( __FILE__ ) );
define( 'CAFEZINHO_WEATHER_URL', plugin_dir_url( __FILE__ ) );

require_once CAFEZINHO_WEATHER_PATH . 'includes/wmo-codes.php';
require_once CAFEZINHO_WEATHER_PATH . 'includes/class-weather-fetcher.php';
require_once CAFEZINHO_WEATHER_PATH . 'includes/class-weather-cache.php';
require_once CAFEZINHO_WEATHER_PATH . 'includes/class-weather-cron.php';
require_once CAFEZINHO_WEATHER_PATH . 'includes/class-weather-widget.php';
require_once CAFEZINHO_WEATHER_PATH . 'includes/class-weather-admin.php';

// Cron schedule + handler.
add_filter( 'cron_schedules', [ 'Cafezinho_Weather_Cron', 'register_schedule' ] );
add_action( Cafezinho_Weather_Cron::HOOK, [ 'Cafezinho_Weather_Cron', 'handle_refresh' ] );

// Activation / deactivation.
register_activation_hook( __FILE__, [ 'Cafezinho_Weather_Cron', 'on_activate' ] );
register_deactivation_hook( __FILE__, [ 'Cafezinho_Weather_Cron', 'on_deactivate' ] );

// Register front-end assets (fonts + plugin css/js).
add_action( 'wp_enqueue_scripts', function () {
    wp_register_style(
        'cafezinho-weather-fonts',
        'https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,300..900,0..100,0..1;1,9..144,300..900,0..100,0..1&family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&family=JetBrains+Mono:wght@400;500&display=swap',
        [],
        null
    );
    wp_register_style(
        'cafezinho-weather',
        CAFEZINHO_WEATHER_URL . 'assets/weather.css',
        [ 'cafezinho-weather-fonts' ],
        CAFEZINHO_WEATHER_VERSION
    );
    wp_register_script(
        'cafezinho-weather',
        CAFEZINHO_WEATHER_URL . 'assets/weather.js',
        [],
        CAFEZINHO_WEATHER_VERSION,
        true
    );
} );

/**
 * Indica se devemos auto-injetar um banner completo (data + edição + widget).
 * Tema custom: define constante ou retorna false no filtro.
 */
function cafezinho_weather_should_auto_inject(): bool {
    if ( defined( 'CAFEZINHO_WEATHER_NO_AUTO' ) && CAFEZINHO_WEATHER_NO_AUTO ) {
        return false;
    }
    return (bool) apply_filters( 'cafezinho_weather_auto_banner', true );
}

/**
 * Banner editorial completo — só renderizado em temas sem integração própria.
 */
function cafezinho_weather_render_fallback_banner(): void {
    if ( ! cafezinho_weather_should_auto_inject() ) {
        return;
    }
    wp_enqueue_style( 'cafezinho-weather' );
    wp_enqueue_script( 'cafezinho-weather' );

    $months = [ '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro' ];
    $weekdays = [ 'Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado' ];
    $now = current_time( 'timestamp' );
    $date_str = sprintf(
        '%s, <span>%02d de %s, %d</span>',
        $weekdays[ (int) gmdate( 'w', $now ) ],
        (int) gmdate( 'j', $now ),
        $months[ (int) gmdate( 'n', $now ) ],
        (int) gmdate( 'Y', $now )
    );
    ?>
    <style>
    .cw-banner {
        border-bottom: 1px solid var(--ink, #2A1812);
        padding: 14px 5vw;
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        gap: 24px;
        font-family: 'JetBrains Mono', ui-monospace, monospace;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--ink-soft, #5A3F35);
        background: var(--bg, #FAF6F0);
    }
    .cw-banner__date span { color: var(--caramelo-deep, #8C4F12); font-weight: 500; }
    .cw-banner__edition { text-align: center; }
    @media (max-width: 768px) {
        .cw-banner { grid-template-columns: 1fr; text-align: center; gap: 6px; padding: 10px 5vw; }
    }
    </style>
    <div class="cw-banner">
        <div class="cw-banner__date"><?php echo wp_kses_post( $date_str ); ?></div>
        <div class="cw-banner__edition">Edição diária</div>
        <?php cafezinho_render_weather_bar(); ?>
    </div>
    <?php
}

// Auto-inject the complete banner when no custom theme has wired things up.
add_action( 'wp_body_open', 'cafezinho_weather_render_fallback_banner' );

// Admin page.
add_action( 'admin_menu', [ 'Cafezinho_Weather_Admin', 'register_menu' ] );
add_action( 'admin_init', [ 'Cafezinho_Weather_Admin', 'handle_actions' ] );
```

- [ ] **Step 2: Syntax check**

Run from `plugins/cafezinho-weather/`:

```
php -l cafezinho-weather.php
```

Expected: `No syntax errors detected`.

- [ ] **Step 3: Commit (Weather_Admin is created in the next task; do not activate the plugin yet)**

```
git add plugins/cafezinho-weather/cafezinho-weather.php
git commit -m "feat(weather): bootstrap plugin with fallback editorial banner injection"
```

---

## Task 14: Weather_Admin page

**Files:**
- Create: `plugins/cafezinho-weather/includes/class-weather-admin.php`

- [ ] **Step 1: Implement Weather_Admin**

`plugins/cafezinho-weather/includes/class-weather-admin.php`:

```php
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
```

- [ ] **Step 2: Syntax check**

Run:

```
php -l includes/class-weather-admin.php
```

Expected: `No syntax errors detected`.

- [ ] **Step 3: Run full test suite (sanity)**

Run:

```
vendor/bin/phpunit
```

Expected: all tests still pass.

- [ ] **Step 4: Commit**

```
git add plugins/cafezinho-weather/includes/class-weather-admin.php
git commit -m "feat(weather): admin page with per-city status + manual refresh"
```

---

## Task 15: Wire plugin into docker-compose

**Files:**
- Modify: `infra/docker-compose.yml`

- [ ] **Step 1: Add the plugin bind-mount**

Modify `infra/docker-compose.yml`. Find this block:

```yaml
    volumes:
      - wp_data:/var/www/html
      # bind mount do tema custom — edita no host, vê no container
      - ./themes/cafezinho:/var/www/html/wp-content/themes/cafezinho
```

Replace with:

```yaml
    volumes:
      - wp_data:/var/www/html
      # bind mount do tema custom — edita no host, vê no container
      - ./themes/cafezinho:/var/www/html/wp-content/themes/cafezinho
      # bind mount do plugin de previsão do tempo
      - ../plugins/cafezinho-weather:/var/www/html/wp-content/plugins/cafezinho-weather
```

(`../plugins/...` because `docker-compose.yml` lives in `infra/`, while the plugin lives in the repo root.)

- [ ] **Step 2: Commit**

```
git add infra/docker-compose.yml
git commit -m "infra: bind-mount cafezinho-weather plugin into WordPress container"
```

---

## Task 16: Live verification

These steps are manual checks against a running WordPress instance, not code.

- [ ] **Step 1: Bring the stack up**

Run from `infra/`:

```
docker compose up -d
```

Expected: 3 containers running (wordpress, db, caddy).

- [ ] **Step 2: Activate the plugin**

Log in to WP admin (`http://localhost/wp-admin`). Go to **Plugins** → activate **Cafezinho Weather**.

Expected: no fatal error; plugin appears as active.

- [ ] **Step 3: Trigger a manual refresh**

Go to **Settings → Cafezinho Weather**. Click **Atualizar agora**.

Expected: success notice; "Última atualização" updates to current time; all 6 cities show recent timestamps and a max/min reading.

- [ ] **Step 4: Verify the bar on the front-end**

Open `http://localhost/` in a browser.

Expected:
- Cream editorial banner at the very top showing date on the left, "Edição diária" centered, and the weather strip on the right.
- Weather strip shows the supra "TEMPO HOJE" + 6 flag/temperature pairs (e.g. `🇬🇧 14° 🇫🇷 22° 🇩🇪 19° 🇪🇸 28° 🇮🇹 26° 🇸🇪 14°`).
- **No panel is open on initial load.**
- Clicking a flag opens a dropdown panel below the strip (does not push the page) with the city name in Fraunces italic, three days of forecast, and the "Fonte · Open-Meteo" footer.
- Clicking the active flag closes the panel.
- Clicking outside the widget closes the panel.
- Pressing `Esc` closes the panel.

- [ ] **Step 5: Verify mobile layout**

Resize browser to <768px (or use device emulation).

Expected:
- Banner becomes a centered single column (date stacked over edition stacked over the weather strip).
- "TEMPO HOJE" supra is hidden.
- Flag tabs wrap into two centered rows if they don't fit one line.
- Dropdown anchors to center with a centered arrow pointer; width is `min(92vw, 360px)`.

- [ ] **Step 6: Verify accessibility basics**

Use browser devtools to inspect the tab buttons.

Expected:
- The strip has `role="tablist"` with `aria-label="Tempo nas capitais europeias"`.
- Each `<button>` has `role="tab"`, `aria-label="<city> <temp> graus"`, and `aria-selected` toggling true/false when active.
- The panel has `role="region"` and `aria-live="polite"`.
- Contrast: ink `#2A1812` on cream `#FAF6F0` passes WCAG AAA.

- [ ] **Step 7: Verify the fallback when API is unreachable**

In **Settings → Cafezinho Weather**, click **Limpar cache**, then immediately reload the front-end **before** the cron fires.

Expected: the strip shows "Tempo carregando…" in italic instead of crashing. Reload again after ~10 seconds — strip should now show real data (single-event refresh fired).

- [ ] **Step 8: Run final test sweep**

Run from `plugins/cafezinho-weather/`:

```
vendor/bin/phpunit
php bin/smoke-weather.php
```

Expected: all unit tests pass; smoke shows 6 ok / 0 falhas.

- [ ] **Step 9: Final commit (only if anything changed during verification)**

If no code changes were needed, skip. Otherwise:

```
git add <files>
git commit -m "fix(weather): <what you fixed during verification>"
```

---

## Done criteria

- [ ] All PHPUnit tests pass (~16 tests across WMO, Fetcher, Cache)
- [ ] `bin/smoke-weather.php` exits 0 with 6 cities OK
- [ ] Live site renders the bar in desktop and mobile
- [ ] Admin page shows 6 cities with recent timestamps
- [ ] Manual "Atualizar agora" works
- [ ] Spec acceptance criteria (§1) met: widget visible on 100% of pageviews, $0 added cost, no crash on API failure
