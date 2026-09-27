# R 라이브러리 자동 복구 (dplyr / rlang.dll 오류)

## 증상
```
> library(dplyr)
에러: package or namespace load failed for 'dplyr' in inDL(x, as.logical(local), as.logical(now), ...):
 공유된 객체 'C:/R/R-4.6.1/library/rlang/libs/x64/rlang.dll'를 로드 할 수 없습니다:
  LoadLibrary failure:  지정된 프로시저를 찾을 수 없습니다.
```

## 사용법 (3단계)
1. **RStudio와 R 창을 모두 닫습니다.** DLL 파일이 사용 중이면 삭제할 수 없습니다.
2. 이 폴더의 `fix_r_library.bat`와 `fix_r_library.R` 두 파일을 **같은 폴더**에 둡니다.
   예: `C:\R\fix\`. 가능하면 경로에 한글이 없는 폴더를 쓰세요.
3. `fix_r_library.bat`를 **더블클릭**합니다.
   - 작업이 끝나면 로그(`C:\R\fix_r_library_log.txt`)가 메모장으로 열립니다.
   - `==== 성공 ====`이 보이면 RStudio를 열고 `library(dplyr)`를 실행하세요.

## 스크립트가 하는 일
| 단계 | 내용 |
|---|---|
| 1 | R 버전, `.libPaths()`, `R_LIBS_USER`, PATH에 섞인 다른 R 버전 진단 |
| 2 | 영문 경로 라이브러리 폴더 생성: `C:\R\library\4.6` |
| 3 | `C:\R\R-4.6.1\etc\Renviron.site`에 `R_LIBS_USER=C:/R/library/%v` 기록. RStudio, RGui, Rscript 모두 같은 경로를 쓰게 됩니다. 기존 `~/.Renviron`에 같은 설정이 있으면 이 값으로 교체합니다. 바꾸기 전 원본은 `.bak`으로 백업합니다. |
| 4 | dplyr와 모든 의존 패키지(rlang, vctrs, cli, glue, pillar, tibble …)의 깨진 설치본 삭제 |
| 5 | R 4.6용 **바이너리**로 재설치. 예전 사용자 라이브러리(한글 경로)에 있던 패키지도 새 경로로 함께 재설치합니다. |
| 6 | **새 R 프로세스**에서 `library(dplyr)`를 실행해 설정이 반영됐는지 검증 |

예전 사용자 라이브러리 폴더는 삭제하지 않습니다. 검색 경로에서만 빠집니다.

## 실패했을 때
`C:\R\fix_r_library_log.txt` 내용을 그대로 전달해 주세요.
