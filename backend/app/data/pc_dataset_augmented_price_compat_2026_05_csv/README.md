# PC 견적 웹용 가격/호환성 추가 CSV 데이터셋

생성일: 2026-05 기준

## 입력 파일
- CPU_UserBenchmarks(1).csv
- GPU_UserBenchmarks(1).csv
- RAM_UserBenchmarks(1).csv
- SSD_UserBenchmarks(1).csv
- HDD_UserBenchmarks(1).csv
- USB_UserBenchmarks(1).csv

## 출력 파일
- CPU_augmented.csv, GPU_augmented.csv, RAM_augmented.csv, SSD_augmented.csv, HDD_augmented.csv, USB_augmented.csv
- Motherboard.csv, Cooler.csv, PSU.csv, Case.csv
- Parts_Master.csv
- Compatibility_Rules.csv
- Compatibility_Pairs.csv
- Summary.csv, Data_Dictionary.csv

## 주의
업로드된 UserBenchmark CSV에는 가격과 정확한 물리 스펙이 없으므로, 가격/소켓/전력/길이/인터페이스는 모델명과 벤치마크를 기반으로 추정했습니다. 실제 결제/구매 화면에서는 실시간 가격 API, 쇼핑몰 크롤링, 관리자 입력값으로 갱신하는 구조를 권장합니다.

## Next.js 사용 예시
1. /data 폴더에 CSV 저장
2. Compatibility_Pairs.csv에서 part_a_id 또는 part_b_id를 기준으로 compatible=TRUE인 항목만 필터링
3. 사용자가 CPU를 선택하면 relation=CPU-Motherboard 또는 CPU-Cooler 기준으로 호환 부품만 노출

## 가격/스펙 참고 소스
자세한 URL은 Source_Notes.csv를 확인하세요. 가격은 실시간 크롤링값이 아니라 2026년 5월 기준 대표 추정가입니다.
