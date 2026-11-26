# Ad Placements & Purchase / IAP Screen Architecture

Complete technical, behavioral, and UI/UX specification for integrating **Ad Placements** and **Purchase / IAP Screens** into any game under the **Beyin-Bedava** framework.

Every rule below reconciles monetization sustainability with the neurobiological and economic protections established in *Algoritmik Etkileşim Mimarisi ve Davranışsal Şartlanma* (Sections 2.2, 2.4, 3.1, 3.2, 5.1, and 6.1).

---

## 1. Ad Placement Architecture (`AdPlacementManager`)

### 1.1 Supported Ad Formats & Strict Behavioral Rules

| Ad Format | Trigger Rule | Forbidden Anti-Patterns | Config Keys |
| :--- | :--- | :--- | :--- |
| **Rewarded Video** | Strictly **opt-in** via explicit player action. Display exact reward amount and daily/session remaining cap before playback. | Never auto-play; never rig DDA (`hit_box`, `damage`, `H_crit`) to manufacture artificial deaths that push "Watch Ad to Revive". | `adPlacements.rewarded` |
| **Interstitial** | Trigger **only at natural boundaries** (level complete, match summary, return to lobby). Enforce onboarding grace (`>= 3` matches/levels), time cooldown (`>= 120s`), and match-count cooldown (`>= 2` matches). **Automatically suppress after `>= 2` consecutive losses** (`L-L` / `L-L-L`) to prevent tilt and respect EOMM churn sensitivity. | Never interrupt mid-action, mid-aim, mid-puzzle, or immediately on loss streaks; never disguise as a "Continue" button. | `adPlacements.interstitial` |
| **Banner** | Display **only on static non-gameplay screens** (Lobby, Pause, Level Select, Match Summary). Enforce `>= 16px` clearance from primary CTAs and reserve fixed layout space. | Never overlay active HUD/gameplay controls; never shift layout right before a tap; never use fake close (`X`) buttons. | `adPlacements.banner` |

### 1.2 Genre-by-Genre Ad Placement Matrix

| Genre | Rewarded Placements (Opt-In) | Interstitial Boundary Windows | Banner Safe Zones |
| :--- | :--- | :--- | :--- |
| **FPS / TPS Shooter** | Post-match 2x soft currency boost; loadout rental trial (disclosed). | Post-match summary exit only (`>= 180s` cooldown, suppressed on 2+ loss streak). | Bottom/top lobby & post-match footer only (hidden in HUD). |
| **Action / Platformer** | Optional checkpoint hint or post-run soft currency bonus (max 1 revive/run, never DDA-forced). | Stage clear / transition screen between chapters (`>= 150s` cooldown). | Main menu / level select edge only. |
| **RPG / Roguelike** | Campfire/tavern bonus reroll or extra daily dungeon key. | Floor/act transition portal (never mid-combat or mid-dialogue). | Town/inventory bottom bar (optional; prefer none during combat). |
| **Puzzle / Match-3 / Casual** | Optional hint, board shuffle, or +3 moves *without* "1 move short" rigged boards. | Every `3+` completed levels (`>= 120s` cooldown, suppressed on 2+ failed attempts). | Static bottom safe-area outside puzzle grid (`>= 16px` margin). |
| **Strategy / Card / Auto-Battler** | Daily shop refresh or extra deck slot trial. | Post-match return-to-menu transition (`>= 180s` cooldown). | Deckbuilder/lobby footer only. |
| **Racing / Sports** | Double career cash reward or cosmetic livery trial. | Post-race podium exit (`>= 150s` cooldown, suppressed on 2+ bottom finishes). | Garage / tournament bracket footer only. |

### 1.3 Engine-Agnostic `AdPlacementManager` Contract & `IAdProvider`

Implement a clean provider boundary so games run out-of-the-box with `MockAdProvider` during local dev/tests and swap cleanly to AdMob, Unity Ads/LevelPlay, AppLovin MAX, or Poki/CrazyGames H5 SDKs:

```text
interface IAdProvider:
  initialize(consentState) -> Promise<bool>
  isAdReady(format, placementId) -> bool
  showRewarded(placementId) -> Promise<{ completed: bool, rewardGranted: bool }>
  showInterstitial(placementId) -> Promise<{ shown: bool, closedAt: timestamp }>
  setBannerVisible(placementId, visible: bool) -> void

class AdPlacementManager:
  canShowInterstitial(playerState, now):
    if entitlement.removeAds: return false
    if playerState.matchesPlayed < config.onboardingGraceMatches: return false
    if playerState.consecutiveLosses >= config.suppressAfterConsecutiveLosses: return false
    if (now - lastInterstitialAt) < config.minIntervalSeconds: return false
    if matchesSinceLastAd < config.minMatchesBetween: return false
    return true
```

### 1.4 Consent, Test IDs & Remove-Ads Synergy
- **Consent First:** Gate personalized ad SDK initialization behind GDPR/UMP and iOS ATT consent state (non-personalized fallback when declined).
- **Test IDs Only by Default:** Never hardcode live production AdMob/AppLovin/Unity ad-unit IDs or API secrets in source code; read from environment/build config and ship official SDK test IDs + `MockAdProvider` as default.
- **Remove-Ads Entitlement:** Purchasing `remove_ads` immediately hides all banners and disables all interstitial triggers while optionally leaving voluntary Rewarded Ads accessible (clearly labeled *"Optional Bonus"*).

---

## 2. Purchase / IAP Screen & Store Architecture (`StoreManager` + Store UI)

### 2.1 Store Screen Anatomy & UX Structure

Design the in-game Store UI as an accessible, clutter-free modal or scene matching the game's art direction:

1. **Top Header Bar:**
   - Current **Soft Currency** (earned) & **Hard Currency** (if used) balances.
   - **"Restore Purchases"** button (mandatory on mobile/storefronts, visibly accessible in header or settings).
   - **"Odds & Fair Play"** quick-link opening the Algorithmic Transparency & Drop-Rate sheet.
2. **Featured / Value Anchor Card:**
   - Typically **"Remove Ads + Starter Kit"** (one-time permanent unlock, real-money price clearly displayed).
3. **Category Navigation Tabs:**
   - `Featured` | `Cosmetics` | `Currency Packs` | `Passes` | `Remove Ads` (adapt tabs to match actual game features; never show empty placeholder tabs).
4. **Product Cards:**
   - Clear item icon, title, concise benefit text, **real-money price** (or exact real-money equivalent alongside virtual currency price), and badge (`Owned`, `Permanent`, or exact non-resetting `Ends in Xd` only if genuinely seasonal).
5. **2-Step Purchase Confirmation Modal:**
   - Summarizes item, exact price in real currency, and cooling-off / spend-cap status.
   - Explicit `[Confirm Purchase]` and `[Cancel]` buttons (`>= 44x44pt` touch targets, full keyboard/gamepad focus navigation).

### 2.2 Anti-Dark-Pattern & Economic Rules (Thesis Sections 2.2, 2.4, 3.2, 5.1)

| Rule | Implementation Requirement | Thesis Grounding |
| :--- | :--- | :--- |
| **Real-Money Equivalent** | When `showRealMoneyEquivalent: true`, render `(~$1.99)` / local currency equivalent beside any hard-currency price tag. | Restores *Pain of Paying* (Prelec & Loewenstein, 1998). |
| **Aligned Currency Bundles** | If hard currency exists, align pack sizes to exact item prices (`preventBundlePriceMismatch: true`) or support direct real-currency SKU checkout so players are not forced into leftover-balance top-ups. | Prevents Sunk Cost & remainder traps (Section 2.4). |
| **No 1-Click Checkout** | Always require the 2-Step Confirmation Modal (`requireTwoStepConfirmation: true`) and honor Layer 4 cooling-off / prepaid spend caps (`layer4_economicCoolingOffHours: 48`). | Layer 4: Economic Isolation (Section 5.1). |
| **Published Drop Odds & Pity** | Any randomized bundle/chest/gacha item MUST link directly to exact percentage odds and live hard-pity counter progress (`showDropOddsAndPity: true`). | Variable Ratio & RPE transparency (Section 3.1). |
| **No Fake Scarcity Timers** | Never ship countdown timers that reset or fabricate urgency (`allowFakeResettingTimers: false`). | FoMO suppression (Holte & Ferraro, 2020). |
| **Zero Commercial Matchmaking Bias** | Keep `matchmaking.weights.gamma_monetization = 0.0`. Never match store browsers with Marquee Players or relax opponent skill post-purchase to manufacture pay-to-win validation. | Activision US20170251672A1 disclosure & neutralization (Section 2.2). |
| **Non-Punitive Passes (Zeigarnik)** | Seasonal/Battle Passes should never expire earned tiers punitively or nag via push notifications (`layer5_suppressZeigarnikNotifications: true`). | Zeigarnik Hygiene (Sections 3.2 & 5.1). |

### 2.3 Engine-Agnostic `StoreManager` Contract & `IIAPProvider`

```text
interface IIAPProvider:
  initialize() -> Promise<bool>
  fetchCatalog(skuIds) -> Promise<List<ProductInfo>>
  purchase(skuId) -> Promise<{ status: "purchased" | "cancelled" | "pending" | "error", receipt }>
  restorePurchases() -> Promise<List<Entitlement>>

class StoreManager:
  requestPurchase(skuId):
    if wellbeing.isEconomicCoolingOffActive():
      return Blocked("48h cooling-off window active")
    if wellbeing.exceedsSpendCap(product.realMoneyValue):
      return Blocked("Player-configured spend cap reached")
    // Open 2-Step Confirmation UI before calling iapProvider.purchase(skuId)
```

Supported production adapters (use `MockIAPProvider` / sandbox by default):
- **Mobile Native:** RevenueCat, Apple StoreKit 2, Google Play Billing v6+, Unity IAP, Godot Android/iOS Billing plugins.
- **Desktop / Console:** Steamworks Microtransactions (`ISteamInventory`), Epic Online Services.
- **Web / H5:** Stripe Checkout / Payment Links (redirect/webhook verified, never client-trusted).

### 2.4 Store UI States & Accessibility Checklist
Every generated or refactored Store UI MUST handle:
- **Loading state** (skeleton/spinner while `fetchCatalog` resolves)
- **Empty / Offline state** (graceful message + Retry button, never blank screen)
- **Pending / Error state** (clear non-punitive feedback for declined/interrupted receipts)
- **Owned / Already Entitled state** (disable duplicate purchase on non-consumables like `remove_ads`)
- **Layer 1 Compatibility:** Store UI remains legible and high-contrast when Grayscale + 40% brightness cap is toggled on (never rely solely on red/green/gold color coding for status or rarity).
