> **2026-11-16追記：ディズニー写真の登録完了。** 既存ピンに1枚追加・保存し、ページ再読み込み後の実写真表示を確認。ピンの追加・削除・位置変更なし。写真62/62件。前日の白紙画面の問題は今回は発生せず、画像URLから登録できた。証跡：`docs/evidence/disneyland-photo-registered.png`。以下の未登録記述は前日時点の履歴。

# 予約先頭表示・雨天分類・ディズニー同期（2026-11-15）

更新先：[My Maps](https://www.google.com/maps/d/viewer?mid=1gKS7F8p3_YdS952P8K2jDE28-1epSAM)／[Sheets](https://docs.google.com/spreadsheets/d/1JNnB15CH_WWwwY7uuopvQabzJhF2sx8v4i8P-G4MOYA/edit)／[写真対応CSV](https://drive.google.com/file/d/1CDP9r8Vdb-lFbL8Kla8vOOGuolvI_MH2/view)。各ファイルIDと地図URLは維持。

## 実施・検証済み

- ユーザーがパリレイヤーに追加した「ディズニーランド パーク」を確認。ピンを追加し直さず、既存ピンに公式情報を入力。地図は62件、都市別15／17／15／13／2件。重複なし。
- 編集前の[バックアップ](https://www.google.com/maps/d/edit?mid=1ee2Rp_U-3xbsEvXKTs8UO50MybN98GM)をMy Mapsの複製機能で作成。
- 全62件の説明を「🎟予約の必要性・公式案内」から始め、☔屋内中心・🌦屋内外あり・🌤屋外中心の印を追記。分類は施設の構造に基づく旅行向け判断であり、雨天時の営業保証ではない。
- My Mapsの保存データを実際にエクスポートし、予約先頭・雨天印62件、5レイヤー、重複なし、既存写真データ61件の維持を確認。読み戻し結果は `data/reservation-weather-map-checks.json`。
- Sheetsは「全62スポット」に変更。パリの一覧にもディズニーを追加。AA「予約の必要性・公式案内」、AB「雨の日・屋内の目安」を全都市へ追加。既存A:Zの値・式は読み戻し比較で保持を確認。
- 写真対応CSVは25列を維持し62件へ更新。メモの先頭に予約・雨天情報を追加。UTF-8 BOM付き、改行はLF。
- 写真番号064は既存GitHub旅程台帳のディズニーIDと一致。062「真実の口」・063「ゴンドラ」のIDは変更しない。Drive一覧の件数62と最大ID064を混同しない。
- ディズニーの実写真を[Drive](https://drive.google.com/file/d/1ZhpsogKv-mlkS42rPmJgfo8eG_8CCXsd/view)へ保存し、Google Driveの画像ビューアで実表示確認。flightlog／CC BY 2.0、2013年撮影の入口。縮小のみ、切り抜きなし。出典のde minimis注記をクレジットにも保存。
- 都市別KML・一括KML・7列インポートCSV・写真出典／クレジット表を同じ62件に更新。ローカルの既存ファイル名に61が残るものは互換パスであり、最新内容は62件。

## ディズニーの確認情報

対象は **Disneyland Park / Parc Disneyland**。Disney Adventure Worldと混同しない。公式券は日付・券種・1パーク／2パークで条件が変わる。日付指定なし券は事前の日付登録が必要。2027年の実料金・営業時間は訪問日未確定のため「要確認」とし、固定額・固定時刻を推測しない。屋外中心なので雨天専用の代替先には分類せず、屋内アトラクションと冬の防寒・雨具を案内。

- [公式パーク案内](https://www.disneylandparis.com/en-int/destinations/disneyland-park)
- [公式チケット](https://tickets.disneylandparis.com/en-int/tickets)
- [公式営業時間](https://www.disneylandparis.com/en-int/calendars/park-hours)
- [入園日登録](https://www.disneylandparis.com/en-int/register-tickets)
- [写真出典・注記](https://commons.wikimedia.org/wiki/File:Disneyland_Park_05,_Paris_22_August_2013.jpg)／[CC BY 2.0](https://creativecommons.org/licenses/by/2.0/)

## 未完了・未検証

- **ディズニーのMy Maps内の写真表示は未登録**。画像追加ダイアログが白紙のまま読み込まれず、直接貼り付けも画像として受け付けられなかった。説明を復元・保存済み。写真はDriveに実在し、KMLには画像指定を用意したが、これを地図内表示成功とは扱わない。
- 地図の写真は61/62件。既存61件は今回データ保持を確認し、前回の個別実表示記録を引き継ぐ。全61枚を今回再撮影したとは扱わない。
- 予約済み・チケット購入済みとは記録していない。実際の予約番号や券面QR等は共有地図へ登録しない。
- スマートフォン実機は未検証。既存写真022・041の再利用許諾は引き続き要確認。
- 別チャットが更新した2027年2月の旅程・出発候補・既存台帳は維持。今回の地図整備によって日付や旅程を確定しない。

## 引き継ぎ

画像追加画面が正常に開く環境で既存のディズニーピンに064写真を1枚追加し、実表示確認後にY列・この記録を更新する。既存のパリKMLをそのまま本番地図へ追加すると重複するため行わない。

検証：`python3 scripts/validate-drive-sync.py`、`node scripts/validate-trip.mjs`、`node scripts/validate-duration.mjs`。実画面の証跡：`docs/evidence/disneyland-map-reservation-weather.png`。
