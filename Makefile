SKILL_DIR := $(HOME)/.claude/skills/termpic

install-skill:
	uv sync
	ln -sfn "$(CURDIR)/skill" "$(SKILL_DIR)"

uninstall-skill:
	rm -f "$(SKILL_DIR)"

.PHONY: install-skill uninstall-skill
