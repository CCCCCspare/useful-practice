# github.io的使用

使用github.io可以将你的项目托管在GitHub上，并通过GitHub Pages进行展示。以下是使用github.io的基本步骤：

## 创建个人专属主页

- 创建一个新的仓库，命名为`<GitHub用户名>.github.io`，例如：`qiwnowinan.github.io`
- 在仓库中创建一个`index.html`文件，这是主页的入口文件，可以使用HTML、CSS和JavaScript来设计主页  
- 将主页内容提交到仓库中，GitHub会自动将其部署为个人主页  
- 访问`https://<GitHub用户名>.github.io`即可查看你的个人主页
- 可以在这个仓库中添加其他文件和资源，如图片、CSS文件等，以丰富主页内容

## 创建项目主页

- 创建一个新的仓库，命名为`<项目名>`，例如：`my-project`
- 在仓库中创建一个`index.html`文件，这是项目主页的入口文件
- 将项目主页内容提交到仓库中，GitHub会自动将其部署为项目主页
- 访问`https://<GitHub用户名>.github.io/<项目名>`即可查看主页
- 可以在这个仓库中添加其他文件和资源，如图片、CSS文件等，以丰富主页内容

## 开启 Pages

- 进入仓库 → Settings → Pages
- Source 选 Deploy from a branch
- Branch 选 main（或你实际默认分支）+ / (root) → Save
