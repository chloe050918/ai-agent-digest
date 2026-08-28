#!/bin/bash
export TERM=xterm-256color
# 清爽版对话式展示：只保留 Codex 的真实推理文字，把工具调用折叠成一行摘要

B=$'\033[1m'      # bold
DIM=$'\033[2m'
CYAN=$'\033[36m'
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
R=$'\033[0m'

say_user() {
  printf "\n${B}${CYAN}▍ 孙璟灿${R}\n%s\n" "$1"
  sleep 1.2
}

say_codex() {
  printf "\n${B}codex${R}\n%s\n" "$1"
  sleep 1.6
}

say_tool() {
  printf "\n${DIM}  ${GREEN}✓${R}${DIM} %s${R}\n" "$1"
  sleep 0.6
}

clear 2>/dev/null; printf "\n"
say_user "output/raw_messages.json 里已经是我今天从飞书 AI资讯 群拉到的真实素材（Phase 1 已完成），帮我从这里开始把内容整理成一期播客，全流程自动跑完，不用等我确认脚本内容。"

say_codex "我会按 ai-agent-digest 工作流，从现有 output/raw_messages.json 直接进入内容筛选、脚本生成、音频合成与产物校验；按你的授权跳过脚本确认。先读取工作流约束和当前工程状态。"

say_tool "读取 SKILL.md · 检索项目记忆 · 确认 4 个 API 凭证已配置"

say_codex "已确认 Phase 1 素材存在，且所需模型与语音凭证均已配置。当前仓库里 synthesize_audio.py 有既存改动，我会保留并基于现状执行，不覆盖用户已有修改；接下来检查各阶段的输入输出契约后直接跑 Phase 2–4。"

say_tool "运行 extract_content.py"

say_codex "浏览器访问也被当前安全策略拦截，无法补取公众号和 X 正文；因此这期的可验证输入实际是「5 个唯一链接，正文 0 条」。我仍会按你的要求自动跑完，但会先去重，并让文字稿明确说明素材缺失边界，只讨论可确认的采集状况与后续阅读优先级，不把链接内容编造成新闻事实。"

say_tool "去重 6→5 条 · 更新 output/materials.json"

say_codex "Phase 3 的方舟接口同样因网络解析失败未能调用。我会使用同一套提示词标准在本地生成一版「透明降级期」：保留日期、双人对话、AI PM 视角与原始链接，但不声称任何未读取到的模型/产品事实。随后直接合成音频，不再停下来等脚本确认。"

say_tool "生成 output/script.md + summary.md"

say_tool "运行 synthesize_audio.py · 云端TTS网络不可达，自动切换本机双音色"

say_codex "脚本与音频已生成，共 20 轮双人对话；云端语音因网络不可达自动切换为本机双音色，完整跑完。现在做最终验收：音频可解码、时长/码率、脚本结构、素材去重和输出文件完整性。"

say_tool "ffprobe 解码校验通过 · 20 轮对话 · 甲/乙轮次平衡"

say_codex "已全流程跑完，产物如下：
  · episode.mp3 — 5 分 33 秒，3.8 MB
  · summary.md — TL;DR 摘要
  · script.md — 双人对话稿
  · materials.json — 6 条转发去重为 5 条

本期为透明降级版：所有原始消息都只有链接、没有可验证正文，因此没有编造具体资讯内容。方舟生成与云端 TTS 均受网络限制，音频已自动改用本机双音色完成合成，并通过完整解码校验。"

sleep 2.5
