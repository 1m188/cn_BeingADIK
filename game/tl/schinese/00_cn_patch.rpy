################################################################################
## Being a DIK — 简体中文汉化补丁 · 补丁框架
##
## 安装方式：将本目录（game/tl/schinese/）整体复制到游戏安装目录的 game/ 下。
## 引擎启动时会自动把 .rpy 编译为 .rpyc，无需手工处理。
##
## 生效机制（已在本游戏 v0.8.3 / Ren'Py 7.4.10 上实测验证）：
##   * 本作启用了样式语句延迟应用：游戏自定义样式在首次 renpy.change_language()
##     时（init_translation 阶段）才真正创建并赋属性，晚于引擎的样式备份；
##   * 因此字体覆盖不能写在 translate <lang> python 块里（那时自定义样式
##     尚不存在，且随后被样式语句覆盖），而是挂接 config.change_language_callbacks：
##     该回调在延迟样式应用完成之后、最终样式重建之前执行，时机恰好；
##   * 每次语言切换收尾时刷新引擎的样式备份（renpy.translation.style_backup），
##     否则第二次切换语言时 restore() 会把延迟创建的全部游戏样式剪掉，
##     导致界面丢失配色与字号；
##   * 切回英文时按记录的原始字体逐项还原，保证双语可逆。
################################################################################

# --------------------------------------------------------------- 补丁配置 --

init -50 python:
    class CNPatchConfig(object):
        # 中文字体：思源黑体 CN（Source Han Sans CN，SIL Open Font License 1.1）
        font       = "tl/schinese/fonts/SourceHanSansCN-Regular.otf"   # 正文 / 界面
        font_bold  = "tl/schinese/fonts/SourceHanSansCN-Bold.otf"      # 人名 / 强调

        # 补丁版本号：变更后会对老用户重新触发一次“自动切中文”
        version = "1.0.0"

        # 游戏自定义样式中硬编码的西文字体 → 原始字体（切回英文时还原用）。
        # 来源：screens.rpy 反编译核对（v0.8.3）。
        style_fonts = {
            "custom_menu_style_header_btn":    "candara.ttf",
            "custom_menu_style_footer_btn":    None,   # 该样式原本未指定字体
            "custom_menu_style_text":          "candara.ttf",
            "custom_menu_style_text2":         "candara.ttf",
            "custom_menu_style_text2_enabled": "candara.ttf",
            "custom_menu_style_text3":         "candara.ttf",
            "slot_text_custom":                "candara.ttf",
            "menu_sex_style":                  "Audrey-Bold.otf",
            "menu_sex_style_disabled":         "Audrey-Bold.otf",
            "badik_input_style2":              "candara.ttf",
        }

        # 引擎根样式的原始字体（切回英文时还原用）
        default_font = "DejaVuSans.ttf"

        # 首次安装 / 升级后自动切换到中文（之后尊重玩家手动选择）
        auto_apply = True

        # 是否显示游戏内右下角的 中/EN 切换角标
        show_badge = True

    cn_patch = CNPatchConfig()


# ------------------------------------------------- 字体应用与语言自动切换 --

init 999 python:
    # 首次安装或补丁升级后，自动把语言切换为中文；
    # 语言偏好由引擎持久化，之后完全尊重玩家的手动选择。
    if persistent.cn_patch_seen != cn_patch.version:
        persistent.cn_patch_seen = cn_patch.version
        if cn_patch.auto_apply:
            _preferences.language = "schinese"

    def cn_patch_apply_fonts():
        """
        语言切换收尾回调（config.change_language_callbacks）。

        执行时机：引擎已应用完全部（延迟的）样式语句之后、
        最终样式重建之前——此时游戏自定义样式必然已存在，
        且我们写入的属性会参与随后的样式构建。

        中文：gui 变量 + 根样式 + 自定义样式全部指向中文字体；
        英文：按 cn_patch 中记录的原始字体逐项还原。
        """
        cn = (_preferences.language == "schinese")

        # 1) 标准 gui 变量（本作 gui.rpy 为标准 gui 体系：
        #    text_font=对话/选项，name_text_font=人名，interface_text_font=界面）
        gui.text_font               = cn_patch.font if cn else "Audrey-Bold.otf"
        gui.name_text_font          = cn_patch.font_bold if cn else "Redressed.ttf"
        gui.interface_text_font     = cn_patch.font if cn else "candara.ttf"
        gui.button_text_font        = gui.interface_text_font
        gui.choice_button_text_font = gui.text_font

        # 2) 根样式兜底：未显式指定字体的文本（含 gui 派生样式）一律继承；
        #    图标字体（symbolfont 等）在各自样式上显式声明，不受影响。
        style.default.font = cn_patch.font if cn else cn_patch.default_font

        # 3) 游戏自定义样式（screens.rpy 中硬编码的西文字体）
        for cn_name, cn_orig in cn_patch.style_fonts.items():
            try:
                cn_st = getattr(style, cn_name)
            except:
                continue
            if cn:
                cn_st.font = cn_patch.font
            elif cn_orig:
                cn_st.font = cn_orig

        # 4) 刷新引擎样式备份：让后续语言切换 restore() 到
        #    “样式齐全”的当前状态，避免延迟创建的样式被剪掉。
        import renpy.translation
        renpy.translation.style_backup = renpy.style.backup()

    config.change_language_callbacks.append(cn_patch_apply_fonts)

    def cn_patch_toggle_language():
        """
        角标动作：在 中文 / 英文 之间切换。
        renpy.change_language 会触发上方回调完成字体切换，
        语言偏好由引擎持久化保存。
        """
        if _preferences.language == "schinese":
            renpy.change_language(None)
        else:
            renpy.change_language("schinese")

    if cn_patch.show_badge:
        config.overlay_screens.append("cn_patch_badge")


# --------------------------------------------------------------- 切换角标 --

screen cn_patch_badge():
    ##
    ## 游戏内右下角的语言切换角标。
    ## 主菜单会抑制 overlay 层，因此角标仅在游戏中显示；
    ## 语言状态由引擎记住，主菜单始终反映当前语言。
    ##
    button:
        xalign 0.995
        yalign 0.992
        background "#00000090"
        hover_background "#000000D0"
        xpadding 12
        ypadding 7
        action Function(cn_patch_toggle_language)
        text "中/EN" font cn_patch.font size 16 color "#E8E8E8"
