"""Phase 5（MVP）：手动触发全链路，跑完在本地生成一期可播放的 mp3"""
import extract_content
import fetch_lark_messages
import generate_script
import synthesize_audio


def main():
    print("=== Phase 1: 拉取飞书消息 ===")
    messages = fetch_lark_messages.fetch()
    if not messages:
        print("过去 24 小时没有采集到消息，退出。")
        return

    print("\n=== Phase 2: 抽取正文 ===")
    materials = extract_content.extract(messages)

    print("\n=== Phase 3: 生成对话脚本 ===")
    script = generate_script.generate(materials)
    print("请先打开 output/summary.md（TL;DR）和 output/script.md（完整对话稿）检查一遍内容，确认没问题再继续合成音频。")
    input("按回车继续合成音频，或 Ctrl+C 中断...")

    print("\n=== Phase 4: 合成音频 ===")
    episode_path = synthesize_audio.synthesize(script)
    print(f"\n全部完成！播放 {episode_path} 试听。")


if __name__ == "__main__":
    main()
