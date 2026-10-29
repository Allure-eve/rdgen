# 在自己的 fork 构建 RustDesk Android 客户端

整理日期：2026-10-29。基于 bryangerlach/rdgen 提交 `073447b88aeeac20ef1811af539b9ed181e1d9cf` 的 Android 工作流修改。保留原项目许可证。

## 这个包做了什么

- 新增 `Standalone Android APK` 工作流，不需要部署 RDGen 网页服务。
- 配置从你仓库的 `RDGEN_BUILD_CONFIG` Secret 读取，不需要作者的 GENURL、ZIP_PASSWORD 或加密配置包。
- 构建结果上传到你自己这次 Actions 的 Artifacts，不上传给作者的生成服务。
- 保留 Kotlin 使用的 `namespace "com.carriez.flutter_hbb"`，只修改安装用的 applicationId，解决本次 `Unresolved reference R` 的触发问题。
- 默认 ARM64，可选择 all 同时构建 ARM64、ARMv7、x86_64。
- 支持自己的 RustDesk 服务器、公钥、应用名称、安装包名、PNG 图标和 custom 高级设置。
- 已做 YAML 解析、actionlint 工作流检查、配置读取和包名修复回归检查；尚未在你的 GitHub 账号执行完整 Android 编译。依赖下载、上游源码或其他补丁仍可能产生另外的错误。

这是供个人 fork 使用的独立构建入口，不能直接将 RDGen 网页导出的完整表单 JSON 当作本包配置。按示例中的结构填写。

## 1. Fork 并启用 Actions

1. 打开 https://github.com/bryangerlach/rdgen ，点右上角 **Fork**，创建到你自己的账号。
2. 打开自己的 `https://github.com/你的用户名/rdgen`。
3. 点 **Actions**，如果提示工作流已禁用，点 **I understand my workflows, go ahead and enable them**。

作者网站提交的任务仍在作者仓库运行；修改 fork 后，要从自己的仓库运行下面的新工作流。

## 2. 把新增文件放进自己的仓库

推荐使用 GitHub Desktop：

1. 安装并登录 GitHub Desktop，选择 **File → Clone repository**，克隆自己的 fork。
2. 打开本地仓库目录。把本包的 `.github` 文件夹复制进去，选择合并文件夹，保留仓库已有的其他文件。
3. 新增文件应是：

```text
你的仓库根目录/
└── .github/
    ├── workflows/
    │   ├── generator-android-standalone.yml
    │   └── bridge-standalone.yml
    └── scripts/
        ├── load-rdgen-config.py
        └── fix-android-app-id.py
```

4. GitHub Desktop 填写提交说明，例如 `Add standalone Android build and fix resource namespace`。
5. 点击 **Commit to master**（以你的默认分支名称为准），再点 **Push origin**。

也可以在 GitHub 网页用 Add file 新建这四个文件，按对应路径复制内容。不要只上传本 ZIP：GitHub 不会自动把 ZIP 里的 workflow 解压运行。

原有 generator-android.yml 保留即可；后面选择新工作流，而不是原来的 Custom Android Client Generator。

## 3. 设置构建配置 Secret

在自己的仓库进入：

**Settings → Secrets and variables → Actions → New repository secret**。

名称填写 `RDGEN_BUILD_CONFIG`，内容按下面填写：

```json
{
  "server": "192.168.31.112",
  "serverPort": 21116,
  "key": "这里替换成当前RustDesk服务端的公钥",
  "appname": "HomeRemote",
  "filename": "home-remote",
  "androidappid": "fun.y1s1.rustdesk",
  "custom": {
    "default-settings": {},
    "override-settings": {}
  }
}
```

| 字段 | 如何填写 |
|---|---|
| server | RustDesk ID 服务器的 IPv4 或域名，不含协议和端口。当前只走内网时用 192.168.31.112 |
| serverPort | hbbs 的 ID 服务端口，通常 21116；本模板按该端口加 1 推导中继端口，适合默认连续端口布局 |
| key | 当前 hbbs 使用的 id_ed25519.pub 内容，Base64 编码的 32 字节 RustDesk 公钥 |
| appname | 界面名称；本模板使用英文字母、数字、下划线、短横线，避免原上游脚本的引号替换问题 |
| filename | APK 文件名前缀，同样使用英文、数字、下划线、短横线 |
| androidappid | 安装标识，示例 fun.y1s1.rustdesk 可与官方默认包名区分。今后升级保持不变 |
| custom | RustDesk 高级设置对象；初次可以保留两个空对象 |

注意：这里需要**现有 RustDesk 服务端公钥**，不是 SSH 公钥/私钥，也不是此前已经丢失匹配私钥的旧 Key。此包不包含你当前的密钥或任何密码。

`192.168.31.112` 只能从家庭内网或已经连通家庭网络的 VPN 访问。构建成功并不会自动让该地址具备公网可达性。

## 4. 可选：自定义图标

把方形 PNG 图片放到自己仓库的：

```text
.github/assets/rdgen-icon.png
```

建议 512×512，至少 256×256。提交并推送即可。没有该文件时保留原图标，不需要配置任何公网图片下载服务。

## 5. 为长期使用配置 APK 签名

RustDesk 的服务端 Key 用于客户端信任服务器；APK 签名用于 Android 判断安装包是否由同一个发布者更新。这是两套不同密钥。

未配置时，上游构建使用 debug 签名，适合测试。今后想稳定地覆盖升级，应从第一次正式分发起使用同一个发布 keystore。重新生成签名或换包名会影响覆盖升级。

在装有 JDK 17 的电脑上，可用 PowerShell：

```powershell
New-Item -ItemType Directory -Force -Path 'D:\Tools\RustDeskBuild'
keytool -genkeypair -v -keystore 'D:\Tools\RustDeskBuild\rustdesk-release.jks' -alias rustdesk -keyalg RSA -keysize 2048 -validity 10000 -storetype JKS
```

按提示设置密码并妥善备份 keystore、alias 和密码。生成 Base64 并复制到剪贴板：

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes('D:\Tools\RustDeskBuild\rustdesk-release.jks')) | Set-Clipboard
```

在仓库的 Actions Secrets 中新增：

| Secret 名称 | 内容 |
|---|---|
| ANDROID_SIGNING_KEY | 刚复制的 keystore Base64 |
| ANDROID_ALIAS | rustdesk |
| ANDROID_KEY_STORE_PASSWORD | keystore 密码 |
| ANDROID_KEY_PASSWORD | alias 对应的密钥密码；若生成时与 keystore 相同，就填同一密码 |

不要将 keystore 或密码提交到 Git 仓库。配置了签名密钥后，签名步骤出错会使任务失败，避免把本应正式签名的测试包当成正式包发布。

如果暂时只验证编译，可以先不设置这四项。以后换正式签名时，之前的测试版可能无法直接覆盖安装。

## 6. 运行并下载

1. 打开自己仓库的 **Actions**。
2. 左侧选择 **Standalone Android APK**。
3. 点击 **Run workflow**，选择包含这四个新增文件的分支。
4. `version` 填要构建的 RustDesk **已有发布标签**，建议先沿用此前构建所选版本；模板初值为 1.5.0。只有该标签真实存在且适配上游脚本时才能成功。先不要改成 master 追开发版。
5. `app_version` 初次留空，不覆盖内置版本。
6. `architectures` 选 **arm64**，适合大多数近年的 Android 手机；需要旧手机或模拟器时选 **all**。
7. 再点 **Run workflow**。
8. 构建完成，进入该次运行的 Summary，页面下方 **Artifacts** 下载 `rustdesk-apk-aarch64`。all 模式还会产生 armv7/x86_64 包。

下载的是 ZIP，解压得到 APK。只有 ARM64 包不能安装到只支持 ARMv7 的旧设备；按目标设备架构选择。

GitHub 托管 runner 首次下载与编译耗时可能超过半小时。公共仓库与私有仓库的 Actions 计费/额度不同，按自己的账号方案核对即可；不需要把 GitHub Token 放进仓库 Secret，这个独立入口使用 GitHub 自动提供的 GITHUB_TOKEN 管理构建产物。

## 维护与排错

- 包名错误对应的步骤变为 `Fix namespace and set custom application ID`，不再使用原来替换整份 build.gradle 包名的方式。
- 如果提示找不到配置，检查 Secret 名称是否严格为 RDGEN_BUILD_CONFIG，以及 JSON 是否有效。
- 如果 key 校验失败，重新复制当前 RustDesk 公钥，不要复制文件路径或 SSH 私钥。
- 若桥接/依赖步骤失败，下载该次完整日志分析；修复 namespace 不代表所有版本的上游依赖都必然兼容。
- 部分 RDGen 补丁仍来自原项目，下载地址固定到本次参考的提交；RustDesk 源码和构建依赖仍会从其原有仓库下载。
- 今后 Sync fork 时检查同名新增文件是否冲突，不要误回到作者原来的在线生成入口。

上游说明：https://github.com/bryangerlach/rdgen/blob/master/setup.md
