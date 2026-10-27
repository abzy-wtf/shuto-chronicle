# Dual-Aspect Taxonomy: Pillars & Motivators



Rivals are classified along two straightforward axes:

1. **The Highway (Macro):** *How they see the road.* (The theater they enter)
2. **The Driver (Micro):** *Why they drive at 2 AM.* (The reason they're out there)

---

## Aspect 1: The Road — How They See the Shuto (Macro)

| Tag ID             | Pillar Name                 | Japanese Concepts | Core Definition & Scope                                                                                                                                                     |
|:------------------ |:--------------------------- |:----------------- |:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`MARTIAL`**      | **Martial Philosophy**      | 武道, 不動心, 独行道, 師弟  | Sovereigns, Bushido, Yagyū/Musashi doctrines, spatial timing (*Maai*), SP battle composure (*Fudōshin*), and master-disciple lineages.                                      |
| **`FEUDAL`**       | **Feudal Allegories**       | 藩閥, 新選組, 戦国, 領地   | Clan structures, Shinsengumi highway patrols, Sengoku/Bakumatsu warlord parallels, territorial retainerships, and dynastic successions.                                     |
| **`SUPERNATURAL`** | **Supernatural & Folklore** | 付喪神, 生霊, 鬼, 供養    | *Tsukumogami* (vessels inhabited by spirits), *Ikiryō* (living astral projections), Oni/Yokai demonology, phantom ghost machines, and Buddhist *Kuyō* memorial reliquaries. |
| **`INDUSTRY`**     | **Industry & Real-World**   | 工房, 調律, 職人, 実在    | Professional tuning houses, aftermarket performance brands, scale model collaborative syndicates, and real-world racing drivers.                                            |

---

## Aspect 2: The Driver — Why They Run (Micro)

| Tag ID         | Motivator Name            | Japanese Concepts | Core Definition & Scope                                                                                                                                                               |
|:-------------- |:------------------------- |:----------------- |:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`GRIEF`**    | **Grief & Loss**          | 喪失, 哀悼, 追悼, 供養    | **Facing the Past with Sorrow.** Driving as a memorial ritual (*Kuyō*) for departed loved ones, lost friends, shattered eras, fatal crash sites, or a lost former self.               |
| **`VENDETTA`** | **Vendetta & Obsession**  | 因縁, 復讐, 執念, 奪還    | **Facing the Past with Rage.** The inability to accept defeat, all-consuming grudges, revanchist score-settling, and toxic obsession with dethroning a rival.                         |
| **`ESCAPE`**   | **The Escape & The Void** | 虚無, 現実逃避, 孤独, 焦燥  | **Fleeing the Mundane Present.** Running from suffocating daylight/salaryman drudgery, existential isolation, mid-life crises, and panic over fading youth (*"time is running out"*). |
| **`BOND`**     | **Devotion & Pure Craft** | 絆, 情熱, 草の根, 求道    | **Building the Future.** Grassroots brotherhood, master-apprentice loyalty, mechanical empathy, and the pursuit of driving as pure dialogue (*"a battle is communication"*).          |

---

## Entity Schema Tagging Format

When tagging rivals, teams, or narrative arcs in manifest processors:

```yaml
taxonomy:
  pillar: "MARTIAL"       # MARTIAL | FEUDAL | SUPERNATURAL | INDUSTRY
  motivator: "BOND"       # GRIEF | VENDETTA | ESCAPE | BOND
  tags: ["sub-concept-1", "sub-concept-2"]
```
