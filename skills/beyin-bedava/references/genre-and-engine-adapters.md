# Genre Adapter Matrix & Engine Integration Blueprints

How to translate EOMM, DDA, behavioral loops, **Ad Placements**, **Purchase/IAP Screens**, transparency, and the 5-layer hygiene protocol into **any game genre and engine**.

---

## 1. Genre Adapter Matrix

| Genre | Matchmaking / Pacing (`EOMM` vs `SBMM`) | `DDA` Equivalent Variables | `RPE`, `Near-Miss` & Ad Loop | `Zeigarnik`, Store/IAP & Protection |
| :--- | :--- | :--- | :--- | :--- |
| **FPS / TPS Shooter** | Team Elo/MMR pairing; avoid `L-L-L` churn traps via balanced lobbies (`sbmm`/`hybrid`). | Hitbox radius $r_{\text{eff}}$ (`<=1.25x`), bullet magnetism $w_{\text{dda}}$, net damage $\Phi$ (`<=1.18x`), $H_{\text{crit}}$ damping. | Opt-in post-match 2x coin Rewarded Ad; post-match Interstitial suppressed after 2+ losses. | Cosmetic-only Store + Remove Ads, real-money pricing, `gamma_monetization = 0.0`, 2-Loss Stop on ranked tilt. |
| **Action / Platformer / Metroidvania** | Single-player pacing director: adjust wave intensity/checkpoint cadence after repeated deaths. | Coyote time & jump buffer extension, hurtbox forgiveness, clutch i-frames below $H_{\text{crit}}$. | Optional post-run coin boost / 1x revive Rewarded Ad (never DDA-forced); chapter-clear Interstitial only. | Assist/Transparency toggle, Campaign/Cosmetic Store, no energy gates on retries. |
| **RPG / Roguelike / ARPG** | Run seed / encounter difficulty director balancing risk vs recovery rooms. | Enemy HP/damage scaling ($\Phi$), crit/dodge pity curves, boss phase recovery pacing. | Tavern/campfire reroll Rewarded Ad; floor-portal Interstitial (`>=150s` cooldown). | Published loot odds + hard pity counter, Grayscale toggle to mute rarity flashes, aligned packs. |
| **Puzzle / Match-3 / Casual** | Level difficulty curve director preventing 3+ hard-wall failures (`L-L-L`). | Piece-spawn favorability weighting, subtle move forgiveness, hint readiness. | Optional hint/shuffle Rewarded Ad; Interstitial every 3+ levels (suppressed on 2+ fails); static bottom Banner (`>=16px` margin). | No "1 move left" rigged FOMO upsells; Remove Ads + Hint Packs in Store; Layer 5 quiet mode. |
| **Strategy / Card / Auto-Battler** | Queue MMR pairing (`SBMM` default for competitive integrity). | PvE AI aggressiveness scaling; transparent casual PvE draw smoothing (never PvP rigging). | Daily shop refresh Rewarded Ad; post-match return-to-menu Interstitial (`>=180s` cooldown). | Exact card/pack odds + hard pity, aligned gem packs or direct currency, 48h spend cooling-off. |
| **Racing / Sports** | Grid/division matchmaking by pace rating. | AI rubber-banding velocity curve, slipstream window width, collision forgiveness. | Double race purse Rewarded Ad; post-podium Interstitial (`>=150s` cooldown). | Label AI Rubber-Banding in Fair Play panel, Cosmetic/Car Pack Store + Remove Ads, 2-Loss Stop. |

---

## 2. Engine Integration Blueprints

Every integration follows a decoupled 6-module layout driven by `beyin-bedava-config.json`:
1. `BeyinBedavaConfig` (loads & validates schema)
2. `TelemetryTracker` (state vector $s_i$, W/L sequence, struggle index, ad/store events)
3. `EngagementDirector` (Matchmaking + DDA + Economy Faucets/Sinks)
4. `AdPlacementManager` + `IAdProvider` (`MockAdProvider` + SDK adapter)
5. `StoreManager` + `StoreUI` + `IIAPProvider` (`MockIAPProvider` + SDK adapter)
6. `WellbeingGuard` (5-Layer Protection + Algorithmic Transparency Panel)

### 2.1 Godot 4 (GDScript / C#)
- **Structure:** Register `res://scripts/beyin_bedava/BeyinBedavaSystem.gd` as an **Autoload** singleton reading `res://config/beyin-bedava-config.json` (plus `AdPlacementManager.gd` & `StoreManager.gd` children).
- **DDA Hook:** Expose `get_hitbox_scale()`, `get_damage_multiplier()`, and `apply_critical_hp_damping(raw_damage, hp_ratio)` queried by `HitboxComponent` / `HealthComponent`.
- **Ad & Store Wiring:** Mount `StoreOverlay.tscn` (`CanvasLayer` layer `90`) with Category Tabs, Real-Currency labels, 2-Step Confirmation Popup, Restore Purchases button, and Fair Play link. Wire `MockAdProvider` / Godot AdMob/Billing plugins via signals (`rewarded_completed`, `purchase_succeeded`).
- **Layer 1 (Visual Cortex Suppression):** Add a top-level `CanvasLayer` (`layer = 100`) with a full-rect `ColorRect` running a grayscale + luminance-cap shader:
  ```glsl
  shader_type canvas_item;
  uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
  uniform float grayscale_amount : hint_range(0.0, 1.0) = 1.0;
  uniform float brightness_cap : hint_range(0.1, 1.0) = 0.4;
  void fragment() {
      vec4 c = texture(screen_tex, SCREEN_UV);
      float luma = dot(c.rgb, vec3(0.299, 0.587, 0.114));
      vec3 mixed = mix(c.rgb, vec3(luma), grayscale_amount);
      COLOR = vec4(mixed * brightness_cap, c.a);
  }
  ```

### 2.2 Unity (C# / URP)
- **Structure:** Place `beyin-bedava-config.json` in `StreamingAssets/` and expose a `DontDestroyOnLoad` `BeyinBedavaManager` service alongside `AdPlacementManager` (LevelPlay/AdMob + `MockAdProvider`) and `StoreManager` (Unity IAP / RevenueCat + `MockIAPProvider`).
- **DDA Hook:** Query `BeyinBedavaManager.Instance.ComputeEffectiveHitboxRadius(baseRadius)` and `ComputeNetDamage(baseDmg, locMult, hpRatio)`.
- **Ad & Store Wiring:** Build a UGUI/UI Toolkit `StorePanel` prefab enforcing `44x44pt+` buttons, safe-area padding (`Screen.safeArea`), 2-step `PurchaseConfirmDialog`, Restore Purchases button, and banner exclusion zones outside gameplay HUD.
- **Layer 1 (Visual Cortex Suppression):** Control a global URP `Volume` containing `ColorAdjustments`: set `saturation.value = -100f` and `postExposure.value` / brightness cap when Layer 1 is enabled.

### 2.3 Unreal Engine 5 (C++ / Blueprint)
- **Structure:** Implement `UBeyinBedavaSubsystem : public UGameInstanceSubsystem` initialized from `Config/beyin-bedava-config.json`, coordinating `UAdPlacementComponent` and `UStoreSubsystem`.
- **Layer 1 (Visual Cortex Suppression):** Bind a global `APostProcessVolume` (`bUnbound = true`) modifying `Settings.ColorSaturation = FVector4(0,0,0,1)` and `ColorGain` to cap luminance at 40%.
- **UI & Protection Hooks:** Expose `BlueprintCallable` functions (`GetDDADamageMultiplier`, `CanShowInterstitial`, `RequestStorePurchase`, `IsTwoLossStopActive`, `GetRemainingFrictionSeconds`) for UMG Store, Transparency, and Well-Being widgets.

### 2.4 Web / TypeScript (Phaser, PixiJS, Three.js, React/Canvas)
- **Structure:** Create a framework-agnostic `src/beyin-bedava/` module (`BeyinBedavaEngine.ts`, `AdPlacementManager.ts`, `StoreManager.ts`, `beyin-bedava-config.json`) + responsive HTML/CSS/React overlay for Store UI, 2-Step Confirmation Modal, Transparency Sheet, and 5-Layer Hygiene toggles.
- **Ad & Store Wiring:** Support H5 ad adapters (Poki/CrazyGames/AdSense H5 + `MockAdProvider`) and Stripe/platform billing (`MockIAPProvider` in dev). Ensure banners sit in dedicated flex containers outside `<canvas>` so zero gameplay tap hijacking occurs.
- **Layer 1 (Visual Cortex Suppression):** Apply CSS filter on the root game container:
  ```css
  .beyin-bedava-grayscale {
    filter: grayscale(100%) brightness(0.4);
    transition: filter 250ms ease;
  }
  ```
