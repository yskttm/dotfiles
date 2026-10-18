# ガイドライン

このファイルは Claude Code と Codex の両方が読む。プロジェクトの AGENTS.md・CLAUDE.md・rules と食い違う場合は、プロジェクト側を優先する。

## コミュニケーション

- 日本語で回答する。一般的に英語表記する語は英語のまま書く（OK: Ruby on Rails、NG: ルビーオンレイルズ）。

## 自律的な進め方

- 依頼を受けたら完了まで止まらずに進める。途中で「続けてよいか」を聞かない。
- 調べればわかること（コード、ログ、コマンドの実行結果、ドキュメント）は自分で調べる。
- 判断に迷ったら妥当な選択肢を選んで進め、選んだ仮定を最後の報告に書く。質問するのは、確かめようがなく、外すと手戻りが大きい仕様や好みの判断だけにする。
- 完了とは、変更を実際に検証した状態を指す。テスト・lint・型チェック・build のうちプロジェクトにあるものを実行して通す。検証できなかったことは、できなかったと報告する。

## 止まって確認する操作

次の操作だけは、実行前に内容を示して確認を取る。それ以外（branch 作成、ファイル編集、commit、feature branch への push、Draft PR の作成）は確認なしで進める。

- デフォルトブランチへの push、force push、履歴の書き換え。
- git 管理外のファイルの上書き・削除。前もって差分を示す。
- 他人の目に触れる書き込み（PR・Issue へのコメント、PR の Ready 化や merge、Slack、Notion など）。
- 本番環境・共有リソース・課金に影響する操作。

## Git

- デフォルトブランチ（main・master・develop）に直接 commit しない。作業は feature branch で行う。
- commit は意味のある単位で分ける。message は英語の Conventional Commits（`<type>(<scope>): <subject>`）にし、subject は命令形で書く。
- 作業が終わったら push し、`gh pr create --draft` で Draft PR を作って URL を示す。
  - Title は英語の Conventional Commits 形式にする。
  - Description は日本語で書き、「概要」「変更内容」「検証結果」を含める。

## 実装

- 新しい振る舞いにはテストを書く。モックは外部依存（API・DB など）にだけ使う。
- 抽象化は3箇所以上で使われてから検討する。
- コメントには「なぜ」だけを書く。未使用のコードと TODO コメントは残さない。
- commit の前に、README・CLAUDE.md・docs/ などとコードに食い違いがないか確認する。あれば同じ PR で直し、`docs` type の commit にする。

<!-- BEGIN AWS Agent Toolkit rules -->
# AWS Guidance
- Where these AWS rules conflict with the project's own instructions, the
  project's instructions take precedence.
- Prefer the AWS MCP Server for AWS interactions — it provides sandboxed
  execution, observability, and audit logging. If unavailable, use the
  AWS CLI directly.
- Before starting a task, check whether a relevant AWS skill is available.
  Load the skill with `retrieve_skill` and prefer its guidance over
  general knowledge.
- When uncertain about specific AWS details (API parameters, permissions,
  limits, error codes), verify against documentation rather than guessing.
  State uncertainty explicitly if you cannot confirm.
- When creating infrastructure, prefer infrastructure-as-code (AWS CDK or
  CloudFormation) over direct CLI commands.
- When working with infrastructure, follow AWS Well-Architected Framework
  principles.
- Do not use em dashes in AWS resource names or descriptions. Use
  hyphens instead.
## Secret Safety

- MUST load the `aws-secrets-manager` skill first for any secret,
  credential, API key, token, or password task. MUST NOT call
  `secretsmanager get-secret-value` or `batch-get-secret-value`, and MUST
  NOT hit the Secrets Manager Agent daemon directly. MUST use
  `{{resolve:secretsmanager:secret-id:SecretString:json-key}}` with
  `asm-exec` so the secret resolves at runtime without entering context.
<!-- END AWS Agent Toolkit rules -->
