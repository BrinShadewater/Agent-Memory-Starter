# 30_Decisions

One file per durable decision. Use `templates/decision-record.md`.

A decision belongs here when it affects architecture, stack, hosting, money, public
messaging, security posture, or anything a future session would otherwise re-litigate
from scratch.

**Two failure modes to watch for.**

The first is that this folder stays empty. It will, for months, unless something forces
the write at the moment the decision is made. Documentation asking people to record
decisions does not work; a prompt at session close asking "what was decided, or
nothing?" does.

The second is the unused **Review Date** field. Every decision template has one. Almost
nobody fills it in, and a decision nobody revisits becomes a constraint nobody chose.
