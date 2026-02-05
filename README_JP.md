# commit2report

GitHub コミットURLからテキスト形式のレポートを生成するCLIツール。OneNoteなどへのコピペに最適化されたフォーマットで出力します。

## 特徴

- 複数のコミットURLを一括処理
- プライベート・パブリックリポジトリ両対応
- 変更ファイル一覧と差分内容を含む詳細レポート
- Jupyter Notebookの変更をサマリー表示（追加/削除行数）
- 差分行数の制限オプション
- コピペしやすいプレーンテキスト出力

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/NaotoKubota/commit2report.git
cd commit2report

# インストール
pip install -e .
```

## セットアップ

1. GitHub Personal Access Token (PAT) を作成
   - https://github.com/settings/tokens にアクセス
   - 「Generate new token (classic)」をクリック
   - スコープ: `repo`（プライベートリポジトリ用）または `public_repo`（パブリックのみ）

2. 環境変数を設定
   ```bash
   # .envファイルを作成
   cp .env.example .env
   
   # .envファイルを編集してトークンを設定
   GITHUB_TOKEN=ghp_your_token_here
   ```

   または、環境変数として直接設定:
   ```bash
   export GITHUB_TOKEN=ghp_your_token_here
   ```

## 使い方

### 基本的な使い方

```bash
# 単一のコミット
commit2report https://github.com/owner/repo/commit/abc1234

# 複数のコミット（異なるリポジトリも可）
commit2report \
  https://github.com/owner/repo1/commit/abc1234 \
  https://github.com/owner/repo2/commit/def5678
```

### ファイルからURLを読み込み

```bash
# commits.txt にURLを1行ずつ記載
commit2report --file commits.txt
```

commits.txt の例:
```
https://github.com/owner/repo1/commit/abc1234
https://github.com/owner/repo2/commit/def5678
https://github.com/owner/repo3/commit/ghi9012
```

### 差分行数を制限

```bash
# 各ファイルの差分を最大50行に制限
commit2report --max-diff-lines 50 https://github.com/owner/repo/commit/abc1234
```

### 詳細モード

```bash
# 詳細（デバッグ）出力を有効化
commit2report --verbose https://github.com/owner/repo/commit/abc1234
```

### 組み合わせ

```bash
# ファイルからURL読み込み + 差分制限 + 追加URL
commit2report --file commits.txt --max-diff-lines 100 https://github.com/extra/repo/commit/xyz
```

## 出力例

```
========================================
Commit Report (2 commits)
Generated: 2026-02-02 10:30:00
========================================

[1/2] owner/repo1
----------------------------------------
Date:    2026-01-15 14:30:25
SHA:     abc1234567890abcdef1234567890abcdef123456
Author:  John Doe <john@example.com>
URL:     https://github.com/owner/repo1/commit/abc1234

Message:
feat: ログイン機能を追加

- OAuth2認証をサポート
- セッション管理を実装

Stats: 2 files changed, +80 insertions, -5 deletions

Changed Files:
────────────────────────────────────────
[M] src/auth/login.py (+70, -5)
────────────────────────────────────────
@@ -10,5 +10,15 @@
 def authenticate():
-    pass
+    """認証処理"""
+    token = get_token()
+    return validate(token)

────────────────────────────────────────
[A] src/auth/session.py (+10, -0)
────────────────────────────────────────
+"""セッション管理モジュール"""
+class Session:
+    pass

========================================

[2/2] owner/repo2
...
```

## ファイルステータスの凡例

- `[A]` - Added (新規追加)
- `[M]` - Modified (変更)
- `[D]` - Deleted (削除)
- `[R]` - Renamed (名前変更)

## トラブルシューティング

### "GITHUB_TOKEN is not set" エラー

環境変数 `GITHUB_TOKEN` が設定されていません。セットアップセクションを参照してください。

### "401 Unauthorized" エラー

トークンが無効か期限切れです。新しいトークンを生成してください。

### "404 Not Found" エラー

- リポジトリが存在しないか、アクセス権がありません
- プライベートリポジトリの場合、トークンに `repo` スコープが必要です

### Rate Limit エラー

GitHub APIのレート制限に達しました。しばらく待ってから再試行してください。

## ライセンス

MIT License
