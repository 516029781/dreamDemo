# V09 控制器放行请求

状态：**等待 V08 独立复核通过**。制作侧不生成密钥、不签名、不改 accepted。

控制器需要：
1. 检查 `sample_release_certificate_request.json` 绑定的 manifest/review/contract 是否为 V08 通过的确切字节。
2. 在制作环境外提供 `ART_HARNESS_REVIEW_KEY`（≥32 字符）或等价外部签名设施；不得让制作模型创建生产密钥。
3. 若 P08 已启用 vNext 证书策略，按合同执行 `tools/art_harness.py certify`；否则由控制器在外部签发绑定当前内容的证书/attestation。
4. 输出 `delivery/next_cycle/T3/sample_release_certificate.json`；若缺密钥或独立 review，保持 waiting_review，不能填 pass。
