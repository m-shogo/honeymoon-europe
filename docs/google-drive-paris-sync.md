# Google Drive 旅行データ：パリ追加（2026-11-14）

## Driveの更新済みファイル
- フォルダ：https://drive.google.com/drive/folders/1uhr7VHc0ufdeSGQjdumf8dbKZstYnoTa
- Google Sheets：https://docs.google.com/spreadsheets/d/1JNnB15CH_WWwwY7uuopvQabzJhF2sx8v4i8P-G4MOYA/edit
- 写真対応CSV：https://drive.google.com/file/d/1CDP9r8Vdb-lFbL8Kla8vOOGuolvI_MH2/view

## 実施した変更
1. 元のスプレッドシートに「パリ」タブを追加：048〜061の14件。
2. 「全47スポット」を「全61スポット」に変更し、既存47件を維持。
3. 既存の写真対応CSVを元のファイルIDのまま61行に更新。25列スキーマを維持。
4. 写真URL・写真出典URLはWikimedia Commonsで実在を確認した個別ファイルページに紐づけた。
5. Google Sheetsの外部画像IMAGE式は外部データアクセス許可がないと #REF! になるため採用せず、Z列に「📷 写真を見る」ハイパーリンクを設定。
6. 写真ファイル本体（048〜061）はGoogle Drive内に未保存。Drive写真リンク列は未登録で空欄とした。写真ファイル名は保存する際の予定名称であり存在を意味しない。
7. 来年の予約時期・曜日が確定した後、営業時間と定休日・2027年料金を公式サイトで再確認する。

## 件数とIDの違い
- Drive 61件＝元の47件＋パリ12件＋モンサンミッシェル2件（048〜061）。
- GitHubの旅行スポット台帳63件＝上記＋ローマの真実の口（062）・ベネチアのゴンドラ（063）。
- 今後Driveを63件へ拡張する際は、062/063のIDを固定し、連番を振り直さない。

## 写真の扱い
- 画像リンクはユーザーが写真と出典へ移動できるように登録。現段階では各画像のDrive内ファイルとしての格納は完了していない。
- 使用する画像のライセンスはWikimedia Commonsの元ページで確認する。