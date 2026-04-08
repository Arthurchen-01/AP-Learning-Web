# AP Mini Tracking App (mini-ap-tracker)

一个基于 **Next.js 15 + Supabase** 的简化版 AP Tracking App。  
目标是提供可直接部署、可持续迭代的 AP 备考进度追踪基础版本，风格偏简洁蓝绿色调（与 samuraiguan.cloud 视觉方向一致）。

---

## 1) 项目说明

当前项目位于仓库子目录：`mini-ap-tracker/`。

已包含的核心能力（当前阶段）：
- Supabase Auth 登录/注册（邮箱密码 + Google OAuth）
- 学生/老师角色入口（student / teacher）
- 使用 `@supabase/ssr` 的 cookie-based auth（`createServerClient` + `getAll/setAll`）
- Dashboard 受保护路由（未登录自动跳转登录页）

后续能力（按规划继续完善）：
- AP 科目与进度 CRUD
- 图表分析（Recharts）
- Realtime 实时刷新
- 每日自动更新数据（Vercel Cron / Supabase 定时任务）

---

## 2) Supabase 项目设置步骤 + 完整 SQL Schema

> 以下步骤建议在 **Supabase Dashboard → SQL Editor** 执行。

### Step A. 创建 Supabase 项目
1. 登录 [Supabase](https://supabase.com/)
2. New project
3. 记录以下信息（稍后填入 `.env.local`）：
   - `Project URL`（`NEXT_PUBLIC_SUPABASE_URL`）
   - `anon public key`（`NEXT_PUBLIC_SUPABASE_ANON_KEY`）

### Step B. 配置 Auth Provider
1. 进入 **Authentication → Providers**
2. 开启 Email
3. 开启 Google（填入 Google OAuth Client ID / Secret）
4. 在 Google Console 中把回调地址加入白名单：
   - 本地：`http://localhost:3000/auth/callback`
   - 线上：`https://<your-domain>/auth/callback`

### Step C. 执行完整 SQL Schema

```sql
-- 建议先启用必要扩展
create extension if not exists pgcrypto;

-- 1) student_profiles
create table if not exists public.student_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  role text not null check (role in ('student', 'teacher')) default 'student',
  grade_level text,
  target_college text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 2) ap_subjects
create table if not exists public.ap_subjects (
  id bigserial primary key,
  name text not null unique,
  category text,
  created_at timestamptz not null default now()
);

-- 3) progress_tracking
create table if not exists public.progress_tracking (
  id bigserial primary key,
  student_id uuid not null references auth.users(id) on delete cascade,
  subject_id bigint not null references public.ap_subjects(id) on delete cascade,
  progress_percent int not null default 0 check (progress_percent >= 0 and progress_percent <= 100),
  latest_mock_score numeric(5,2),
  notes text,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique(student_id, subject_id)
);

-- 更新时间触发器函数
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- 触发器绑定

drop trigger if exists trg_student_profiles_updated_at on public.student_profiles;
create trigger trg_student_profiles_updated_at
before update on public.student_profiles
for each row execute function public.set_updated_at();

drop trigger if exists trg_progress_tracking_updated_at on public.progress_tracking;
create trigger trg_progress_tracking_updated_at
before update on public.progress_tracking
for each row execute function public.set_updated_at();

-- 初始化 AP 科目（可按需增删）
insert into public.ap_subjects (name, category)
values
  ('Calculus AB', 'Math'),
  ('Calculus BC', 'Math'),
  ('Biology', 'Science'),
  ('Chemistry', 'Science'),
  ('Physics 1', 'Science'),
  ('Computer Science A', 'CS'),
  ('Statistics', 'Math'),
  ('Microeconomics', 'Social Science'),
  ('Macroeconomics', 'Social Science'),
  ('US History', 'History')
on conflict (name) do nothing;

-- RLS
alter table public.student_profiles enable row level security;
alter table public.ap_subjects enable row level security;
alter table public.progress_tracking enable row level security;

-- student_profiles: 用户可读写自己的 profile
create policy "read own profile"
on public.student_profiles
for select
using (auth.uid() = id);

create policy "insert own profile"
on public.student_profiles
for insert
with check (auth.uid() = id);

create policy "update own profile"
on public.student_profiles
for update
using (auth.uid() = id)
with check (auth.uid() = id);

-- ap_subjects: 已登录用户可读
create policy "read subjects for authenticated"
on public.ap_subjects
for select
using (auth.role() = 'authenticated');

-- progress_tracking: 用户仅可读写自己的进度
create policy "read own progress"
on public.progress_tracking
for select
using (auth.uid() = student_id);

create policy "insert own progress"
on public.progress_tracking
for insert
with check (auth.uid() = student_id);

create policy "update own progress"
on public.progress_tracking
for update
using (auth.uid() = student_id)
with check (auth.uid() = student_id);

create policy "delete own progress"
on public.progress_tracking
for delete
using (auth.uid() = student_id);

-- Realtime（用于后续前端实时订阅）
alter publication supabase_realtime add table public.progress_tracking;
```

---

## 3) Vercel 部署步骤（重点：Root Directory）

1. 打开 [Vercel](https://vercel.com/) 并导入该 GitHub 仓库。
2. 在 **Project Settings → General** 里设置：
   - **Root Directory: `mini-ap-tracker`**（必须）
3. Framework 会自动识别为 Next.js。
4. 在 **Environment Variables** 中填入（见下一节）。
5. 点击 Deploy。
6. 部署完成后，把线上域名加入 Supabase Auth Redirect URL：
   - `https://<your-vercel-domain>/auth/callback`

---

## 4) 环境变量怎么填

在 `mini-ap-tracker/.env.local` 中填写：

```bash
NEXT_PUBLIC_SUPABASE_URL=https://<your-project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

线上（Vercel）请设置：

```bash
NEXT_PUBLIC_SUPABASE_URL=https://<your-project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
NEXT_PUBLIC_SITE_URL=https://<your-vercel-domain>
```

> `NEXT_PUBLIC_SITE_URL` 用于 OAuth 回调地址拼接，必须与实际访问域名一致。

---

## 5) 本地运行命令

在仓库根目录执行：

```bash
cd mini-ap-tracker
npm install
npm run dev
```

打开：`http://localhost:3000`

可选检查：

```bash
npm run typecheck
npm run lint
npm run build
```

---

## 6) 如何开启每日自主更新（Daily Auto Update）

推荐方案：**Vercel Cron + Next.js Route Handler**。

### Step A. 新增一个定时 API（示例）
建议后续新增：`app/api/cron/daily-progress/route.ts`，逻辑为：
- 校验 `Authorization: Bearer <CRON_SECRET>`
- 随机选 1~2 个 student + subject
- 将 `progress_percent` 增加 1~5（不超过 100）
- 更新 `latest_mock_score` / `notes` / `updated_at`

### Step B. 在 `vercel.json` 配置 Cron
当前 `mini-ap-tracker/vercel.json` 可扩展为：

```json
{
  "crons": [
    {
      "path": "/api/cron/daily-progress",
      "schedule": "0 0 * * *"
    }
  ]
}
```

> 上述是 UTC 0 点（北京时间 08:00）。如果你想按中国本地凌晨，可改成 `0 16 * * *`（UTC 16:00 = 北京时间 00:00）。

### Step C. 配置密钥
在 Vercel 环境变量增加：
- `CRON_SECRET=<a-strong-random-string>`

然后在 Cron API 内校验该密钥，避免被外部随意调用。

---

## 目录说明（当前）

```text
mini-ap-tracker/
├─ app/
│  ├─ (auth)/
│  │  ├─ login/page.tsx
│  │  ├─ register/page.tsx
│  │  └─ actions.ts
│  ├─ auth/callback/route.ts
│  ├─ dashboard/page.tsx
│  ├─ globals.css
│  ├─ layout.tsx
│  └─ page.tsx
├─ lib/
│  ├─ env.ts
│  └─ supabase/
│     ├─ client.ts
│     ├─ server.ts
│     └─ middleware.ts
├─ types/database.ts
├─ middleware.ts
├─ package.json
├─ tsconfig.json
├─ .env.example
└─ vercel.json
```

---

如需我继续下一步，我会在下一次 PR 中补齐：
1) `progress_tracking` CRUD + 表格排序  
2) Recharts 分析卡片  
3) Realtime 自动刷新  
4) `app/api/cron/daily-progress` 的完整实现
