# RMT 平台公网部署指南 (Vercel + Render/Railway)

为了实现最专业的公网访问体验，我们采用 **Vercel (前端)** + **Render/Railway (后端)** 的黄金组合。

---

## 步骤 1：部署 Python 后端 (Render 或 Railway)

建议先部署后端，以获取公网 API 地址。

### 选项 A：使用 Render.com (推荐)
1. 登录 [Render.com](https://render.com/)。
2. 点击 **"New +" -> "Blueprint"**。
3. 连接 GitHub 仓库并选择 `RMT`。
4. Render 会自动识别根目录的 `render.yaml` 并启动部署。
5. **获取 URL**：部署成功后，你会得到一个类似 `https://rmt-backend-xxx.onrender.com` 的地址。

### 选项 B：使用 Railway.app
1. 登录 [Railway.app](https://railway.app/)。
2. 点击 **"New Project" -> "Deploy from GitHub repo"**。
3. 选中 `RMT` 仓库。
4. 在 Variables 设置中，如果报错，请确保添加 `PORT` 变量（通常 Railway 会自动处理）。
5. **获取 URL**：在 Settings 选项卡下生成一个 Domain。

---

## 步骤 2：部署 Vue 前端 (Vercel)

Vercel 是目前最强大的前端托管平台，支持代码推送即发布。

1. 登录 [Vercel.com](https://vercel.com/)。
2. 点击 **"Add New" -> "Project"**。
3. 导入您的 GitHub 仓库 `RMT`。
4. **关键配置**：
   - **Framework Preset**: 选择 `Vite`。
   - **Root Directory**: 选择 `frontend` (非常重要！)。
   - **Environment Variables**: 展开此项，添加一个新的变量：
     - **Key**: `VITE_API_BASE_URL`
     - **Value**: 填入您在步骤 1 中拿到的**后端公网 URL** (例如 `https://rmt-backend-xxx.onrender.com`)。
5. 点击 **"Deploy"**。

---

## 步骤 3：后续更新

以后您只要在本地修改代码并 `git push`：
1. **前端**：Vercel 会感知到 `frontend` 文件夹的变化并自动重新打包。
2. **后端**：Render/Railway 会感知到 `backend` 或 `requirements.txt` 的变化并自动重启服务。

**现在您的平台已经拥有了真正的生产级部署架构！快去 Vercel 分享您的网址吧！**
