# ガイドライン

このファイルは Claude Code と Codex の両方が読む。プロジェクトの AGENTS.md・CLAUDE.md・rules と食い違う場合は、プロジェクト側を優先する。

## コミュニケーション

- 日本語で回答する。プログラミングで一般に英語表記する語は英語のまま書く（OK: Ruby on Rails、NG: ルビーオンレイルズ）。
- コードを読む、コマンドを実行するなどで確かめられることは自分で確かめる。質問するのは、仕様や好みのように確かめようがなく、外すと手戻りが大きい判断だけにする。

## 確認が必要な操作

次の操作の前は、内容を示して確認を取る。ブランチ作成、ファイル編集、ローカルでの commit は確認なしで進めてよい。

- push。前もって変更ファイルの一覧を示す。
- git 管理外のファイルの上書き・削除。前もって差分を示す。
- 外部サービスへの書き込み（PR コメント、Slack、Notion など）。

## Git

- デフォルトブランチ（main・master・develop）に直接 commit しない。作業は feature branch で行う。
- commit message は英語の Conventional Commits（`<type>(<scope>): <subject>`）にし、subject は命令形で書く。
- push したら確認を待たずに `gh pr create --draft` で Draft PR を作り、URL を示す。
  - Title は英語の Conventional Commits 形式にする。
  - Description は日本語で書き、「概要」「変更内容」「検証結果」を含める。

## 実装

- 新しい振る舞いにはテストを書き、テストが通るまで直す。モックは外部依存（API・DB など）にだけ使う。
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
