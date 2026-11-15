# ====================================================================
#  fix_r_library.R  -  R 패키지 라이브러리 자동 복구 (dplyr / rlang DLL 오류)
#
#  증상:
#    library(dplyr)
#    'C:/R/R-4.6.1/library/rlang/libs/x64/rlang.dll' 를 로드 할 수 없습니다
#    LoadLibrary failure: 지정된 프로시저를 찾을 수 없습니다.
#
#  하는 일 (모두 자동):
#    1) 현재 R 설치/라이브러리 경로 진단
#    2) 영문 전용 라이브러리 폴더 생성   예) C:/R/library/4.6
#    3) R_HOME/etc/Renviron.site 에 R_LIBS_USER 고정 (+ ~/.Renviron 충돌 줄 정리)
#       -> RStudio/RGui/Rscript 어디서 실행해도 같은 라이브러리를 사용
#    4) dplyr 와 그 의존 패키지(rlang, vctrs, cli ...)의 깨진 설치본 삭제
#    5) 새 라이브러리에 R 버전에 맞는 바이너리로 재설치
#       (+ 예전 사용자 라이브러리에 있던 패키지도 함께 재설치)
#    6) 새 R 프로세스에서 library(dplyr) 가 되는지 검증
#
#  실행 방법: RStudio 를 완전히 종료한 뒤 fix_r_library.bat 더블클릭
#            (또는 RGui 에서 source("fix_r_library.R", encoding = "UTF-8"))
#  결과 로그: <R 설치 상위 폴더>/fix_r_library_log.txt   예) C:/R/fix_r_library_log.txt
# ====================================================================

local({

options(repos = c(CRAN = Sys.getenv("FIX_R_REPOS", "https://cloud.r-project.org")),
        install.packages.check.source = "no",
        timeout = max(600, getOption("timeout")))

np <- function(p) normalizePath(p, winslash = "/", mustWork = FALSE)
is_writable <- function(d) dir.exists(d) && file.access(d, 2) == 0

# ---- 경로 결정 ------------------------------------------------------
ver     <- paste(R.version$major, sub("\\..*$", "", R.version$minor), sep = ".")   # "4.6"
r_home  <- np(R.home())                                    # C:/R/R-4.6.1
sys_lib <- np(.Library)                                    # C:/R/R-4.6.1/library
lib_root <- file.path(dirname(r_home), "library")          # C:/R/library
dir.create(file.path(lib_root, ver), recursive = TRUE, showWarnings = FALSE)
if (!is_writable(file.path(lib_root, ver))) {              # C:/R 에 쓰기 불가 -> C:/Rlib
  lib_root <- file.path(Sys.getenv("SystemDrive", "C:"), "Rlib")
  dir.create(file.path(lib_root, ver), recursive = TRUE, showWarnings = FALSE)
}
new_lib  <- np(file.path(lib_root, ver))
old_libs <- setdiff(np(.libPaths()), c(sys_lib, new_lib))  # 기존 사용자 라이브러리(한글 경로 등)

# ---- 로그 (화면 + 파일 동시 출력) -----------------------------------
log_file <- file.path(dirname(lib_root), "fix_r_library_log.txt")
if (!is_writable(dirname(log_file))) log_file <- file.path(new_lib, "fix_r_library_log.txt")
log_con <- file(log_file, open = "wt", encoding = "UTF-8")
sink(log_con, split = TRUE)
on.exit({ sink(); close(log_con) }, add = TRUE)

say  <- function(...) cat(..., "\n", sep = "")
step <- function(n, ...) say("\n[", n, "/6] ", ...)

say("==== R 라이브러리 자동 복구  ", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), " ====")

# ---- 1) 진단 --------------------------------------------------------
step(1, "현재 상태 진단")
say("  R 버전        : ", R.version.string)
say("  R_HOME        : ", r_home)
say("  시스템 라이브러리 : ", sys_lib)
say("  기존 .libPaths : ", paste(np(.libPaths()), collapse = "  |  "))
say("  R_LIBS_USER   : ", Sys.getenv("R_LIBS_USER"))
if (nzchar(Sys.getenv("R_LIBS")))
  say("  [주의] 환경변수 R_LIBS 가 설정되어 있음: ", Sys.getenv("R_LIBS"))
loaded <- intersect(c("rlang", "vctrs", "cli", "dplyr"), loadedNamespaces())
if (length(loaded))
  say("  [주의] 이 세션에 이미 로드됨: ", paste(loaded, collapse = ", "),
      "  -> RStudio 안에서 실행하면 파일 잠김으로 실패할 수 있음")
other_r <- grep("[\\\\/]R-[0-9.]+[\\\\/]bin", strsplit(Sys.getenv("PATH"), .Platform$path.sep)[[1]],
                value = TRUE)
other_r <- other_r[!startsWith(np(other_r), r_home)]
if (length(other_r))
  say("  [주의] PATH 에 다른 R 버전 bin 이 있음: ", paste(other_r, collapse = " ; "))

# ---- 2) 새 라이브러리 폴더 -------------------------------------------
step(2, "영문 전용 라이브러리 폴더 준비")
say("  새 라이브러리 : ", new_lib)

# ---- 3) R_LIBS_USER 영구 고정 ----------------------------------------
step(3, "R_LIBS_USER 영구 설정")
env_line <- sprintf("R_LIBS_USER=%s/%%v", np(lib_root))          # %v -> R 버전(4.6)

set_env_line <- function(f, line = env_line, add_if_missing = TRUE) {
  old <- if (file.exists(f)) readLines(f, warn = FALSE, encoding = "UTF-8") else character()
  has <- grepl("^\\s*R_LIBS_USER\\s*=", old)
  if (!any(has) && !add_if_missing) return(invisible(FALSE))
  if (file.exists(f)) file.copy(f, paste0(f, ".bak"), overwrite = TRUE)
  ok <- tryCatch({ writeLines(c(old[!has], line), f, useBytes = TRUE); TRUE },
                 error = function(e) FALSE, warning = function(w) FALSE)
  if (ok) say("  기록 완료     : ", f, "  ->  ", line)
  ok
}

site_env <- file.path(r_home, "etc", "Renviron.site")
site_ok  <- is_writable(dirname(site_env)) && set_env_line(site_env)
user_env <- np(path.expand("~/.Renviron"))
# 사용자 .Renviron 은 site 설정보다 우선 -> R_LIBS_USER 줄이 있으면 같은 값으로 교체,
# site 파일에 쓰지 못했으면 사용자 파일에 새로 기록
set_env_line(user_env, add_if_missing = !site_ok)

site_prof <- file.path(r_home, "etc", "Rprofile.site")
for (pf in c(site_prof, path.expand("~/.Rprofile")))
  if (file.exists(pf) && any(grepl("\\.libPaths\\s*\\(", readLines(pf, warn = FALSE))))
    say("  [주의] ", np(pf), " 안에 .libPaths() 설정이 있음 -> 경로를 덮어쓸 수 있으니 확인 필요")

# 이 프로세스도 즉시 새 경로 사용 (기존 사용자 라이브러리는 검색 경로에서 제외)
.libPaths(new_lib)
say("  현재 .libPaths : ", paste(np(.libPaths()), collapse = "  |  "))

# ---- 4) 깨진 설치본 삭제 --------------------------------------------
step(4, "dplyr 의존 패키지의 기존(깨진) 설치본 삭제")
db <- tryCatch(available.packages(),
               error = function(e) stop("CRAN 접속 실패 - 인터넷 연결/방화벽을 확인하세요: ",
                                        conditionMessage(e)))
base_pk <- rownames(installed.packages(lib.loc = sys_lib, priority = c("base", "recommended")))
deps <- tools::package_dependencies("dplyr", db = db, recursive = TRUE,
                                    which = c("Depends", "Imports", "LinkingTo"))[["dplyr"]]
core <- setdiff(unique(c("dplyr", deps)), base_pk)
say("  대상 (", length(core), "개): ", paste(sort(core), collapse = ", "))

failed <- character()
for (lib in unique(c(new_lib, sys_lib))) {
  if (!dir.exists(lib)) next
  unlink(list.files(lib, "^00LOCK", full.names = TRUE), recursive = TRUE, force = TRUE)
  for (p in intersect(core, list.files(lib))) {
    unlink(file.path(lib, p), recursive = TRUE, force = TRUE)
    if (dir.exists(file.path(lib, p))) failed <- c(failed, file.path(lib, p))
  }
}
if (length(failed)) {
  say("  [경고] 삭제하지 못한 폴더 (파일 잠김 또는 권한 부족):")
  for (f in failed) say("         ", f)
  if (any(startsWith(failed, new_lib)))
    stop("RStudio / R 창을 모두 닫고 다시 실행하세요 (DLL 파일이 사용 중입니다).")
  say("  -> 새 라이브러리가 검색 순서상 앞이므로 계속 진행합니다.")
} else say("  삭제 완료")

# ---- 5) 재설치 ------------------------------------------------------
step(5, "R ", ver, " 용 바이너리 재설치")
old_pkgs <- unique(unlist(lapply(old_libs[dir.exists(old_libs)],
                                 function(l) rownames(installed.packages(lib.loc = l)))))
carry <- setdiff(intersect(old_pkgs, rownames(db)), c(core, base_pk))
if (length(carry))
  say("  예전 사용자 라이브러리에서 옮겨올 패키지 (", length(carry), "개): ",
      paste(sort(carry), collapse = ", "))
targets <- c(core, carry)
bin_type <- if (.Platform$OS.type == "windows") "binary" else getOption("pkgType")
install.packages(targets, lib = new_lib, type = bin_type, dependencies = NA)
missing <- setdiff(targets, rownames(installed.packages(lib.loc = new_lib)))
if (length(missing)) say("  [경고] 설치되지 않은 패키지: ", paste(missing, collapse = ", "))

# ---- 6) 새 프로세스에서 검증 ----------------------------------------
step(6, "새 R 프로세스에서 library(dplyr) 검증 (Renviron 설정 반영 여부 포함)")
rscript <- file.path(R.home("bin"), if (.Platform$OS.type == "windows") "Rscript.exe" else "Rscript")
chk <- file.path(new_lib, "_verify_dplyr.R")
writeLines(c(
  'cat("LIBPATHS:", paste(normalizePath(.libPaths(), winslash = "/"), collapse = " | "), "\\n")',
  'suppressPackageStartupMessages(library(dplyr))',
  'cat("RLANG   :", normalizePath(find.package("rlang"), winslash = "/"), as.character(packageVersion("rlang")), "\\n")',
  'cat("DPLYR_OK:", as.character(packageVersion("dplyr")), "\\n")'
), chk)
Sys.unsetenv("R_LIBS_USER")   # 새로 켠 R 과 같은 조건: Renviron 파일에서만 경로를 읽게 함
out <- suppressWarnings(system2(rscript, shQuote(chk), stdout = TRUE, stderr = TRUE))
unlink(chk)
for (l in out) say("  ", l)

rlang_line <- grep("^RLANG", out, value = TRUE)
if (any(grepl("^DPLYR_OK", out)) && length(rlang_line) && grepl(new_lib, rlang_line, fixed = TRUE)) {
  say("\n==== 성공: library(dplyr) 정상 로드 ====")
  say("RStudio 를 다시 열고 콘솔에서 library(dplyr) 를 실행해 보세요.")
  say("(RStudio 가 열려 있었다면 Session > Restart R  또는 Ctrl+Shift+F10)")
} else {
  say("\n==== 실패: 위 검증 출력과 이 로그 파일을 그대로 전달해 주세요 ====")
  say("로그: ", np(log_file))
}
say("로그 파일: ", np(log_file))

})
