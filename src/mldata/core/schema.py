"""Schema evolution service for tracking schema changes across builds."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Type of schema change."""

    ADDED = "added"
    REMOVED = "removed"
    TYPE_CHANGED = "type_changed"
    NULLABLE_CHANGED = "nullable_changed"


class SchemaColumn(BaseModel):
    """Schema column information."""

    name: str
    dtype: str
    nullable: bool = False


class ColumnChange(BaseModel):
    """Change to a single column."""

    column: str
    change_type: ChangeType
    old_value: str | None = None
    new_value: str | None = None


class SchemaEvolution(BaseModel):
    """Schema evolution report."""

    version: str = "1.0"
    generated_at: datetime
    baseline_path: str = ""
    current_path: str = ""
    baseline_columns: list[SchemaColumn] = Field(default_factory=list)
    current_columns: list[SchemaColumn] = Field(default_factory=list)
    added_columns: list[SchemaColumn] = Field(default_factory=list)
    removed_columns: list[SchemaColumn] = Field(default_factory=list)
    type_changes: list[ColumnChange] = Field(default_factory=list)
    nullable_changes: list[ColumnChange] = Field(default_factory=list)
    breaking_changes: list[ColumnChange] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)

    def to_json(self, path: str) -> None:
        """Export report to JSON."""
        import json

        with open(path, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2)

    def to_markdown(self, path: str | None = None) -> str:
        """Generate markdown report.

        Args:
            path: Optional path to write file

        Returns:
            Markdown string
        """
        lines = [
            "# Schema Evolution Report",
            f"**Generated:** {self.generated_at.isoformat()}",
            "",
            "## Overview",
            f"- Baseline: {self.baseline_path}",
            f"- Current: {self.current_path}",
            f"- Baseline columns: {len(self.baseline_columns)}",
            f"- Current columns: {len(self.current_columns)}",
            f"- Breaking changes: {len(self.breaking_changes)}",
            "",
            "## Summary",
            f"- Added: {self.summary.get('added', 0)}",
            f"- Removed: {self.summary.get('removed', 0)}",
            f"- Type changes: {self.summary.get('type_changed', 0)}",
            f"- Nullable changes: {self.summary.get('nullable_changed', 0)}",
            "",
        ]

        if self.added_columns:
            lines.append("## Added Columns")
            lines.append("")
            lines.append("| Name | Type | Nullable |")
            lines.append("|------|------|----------|")
            for col in self.added_columns:
                lines.append(f"| {col.name} | {col.dtype} | {'Yes' if col.nullable else 'No'} |")
            lines.append("")

        if self.removed_columns:
            lines.append("## Removed Columns")
            lines.append("")
            lines.append("| Name | Type | Nullable |")
            lines.append("|------|------|----------|")
            for col in self.removed_columns:
                lines.append(f"| {col.name} | {col.dtype} | {'Yes' if col.nullable else 'No'} |")
            lines.append("")

        if self.type_changes:
            lines.append("## Type Changes")
            lines.append("")
            lines.append("| Column | Old Type | New Type |")
            lines.append("|--------|----------|----------|")
            for change in self.type_changes:
                lines.append(f"| {change.column} | {change.old_value} | {change.new_value} |")
            lines.append("")

        if self.nullable_changes:
            lines.append("## Nullable Changes")
            lines.append("")
            lines.append("| Column | Old | New |")
            lines.append("|--------|-----|-----|")
            for change in self.nullable_changes:
                lines.append(f"| {change.column} | {change.old_value} | {change.new_value} |")
            lines.append("")

        if self.breaking_changes:
            lines.append("## Breaking Changes")
            lines.append("")
            lines.append("[red]Warning: These changes may break downstream pipelines[/]")
            lines.append("")
            for change in self.breaking_changes:
                lines.append(f"- {change.column}: {change.change_type.value}")
            lines.append("")

        output = "\n".join(lines)

        if path:
            with open(path, "w") as f:
                f.write(output)

        return output


class SchemaEvolutionService:
    """Service for tracking schema evolution across builds."""

    # Breaking type changes (changes that may cause runtime errors)
    BREAKING_TYPE_CHANGES = {
        ("int", "str"): True,
        ("float", "str"): True,
        ("str", "int"): True,
        ("str", "float"): True,
        ("list", "str"): True,
        ("dict", "str"): True,
    }

    def compare_schemas(
        self,
        baseline_columns: list[SchemaColumn],
        current_columns: list[SchemaColumn],
    ) -> SchemaEvolution:
        """Compare two schemas and identify changes.

        Args:
            baseline_columns: Columns from baseline schema
            current_columns: Columns from current schema

        Returns:
            SchemaEvolution with all changes
        """
        baseline_map = {c.name: c for c in baseline_columns}
        current_map = {c.name: c for c in current_columns}

        evolution = SchemaEvolution(
            generated_at=datetime.now(),
            baseline_columns=baseline_columns,
            current_columns=current_columns,
        )

        # Find added columns
        for col in current_columns:
            if col.name not in baseline_map:
                evolution.added_columns.append(col)

        # Find removed columns
        for col in baseline_columns:
            if col.name not in current_map:
                evolution.removed_columns.append(col)

        # Find type and nullable changes
        for name in baseline_map:
            if name in current_map:
                old_col = baseline_map[name]
                new_col = current_map[name]

                # Type change
                if old_col.dtype != new_col.dtype:
                    change = ColumnChange(
                        column=name,
                        change_type=ChangeType.TYPE_CHANGED,
                        old_value=old_col.dtype,
                        new_value=new_col.dtype,
                    )
                    evolution.type_changes.append(change)

                    # Check if breaking
                    if self._is_breaking_type_change(old_col.dtype, new_col.dtype):
                        evolution.breaking_changes.append(change)

                # Nullable change
                if old_col.nullable != new_col.nullable:
                    change = ColumnChange(
                        column=name,
                        change_type=ChangeType.NULLABLE_CHANGED,
                        old_value=str(old_col.nullable),
                        new_value=str(new_col.nullable),
                    )
                    evolution.nullable_changes.append(change)

        # Summary
        evolution.summary = {
            "added": len(evolution.added_columns),
            "removed": len(evolution.removed_columns),
            "type_changed": len(evolution.type_changes),
            "nullable_changed": len(evolution.nullable_changes),
        }

        return evolution

    def _is_breaking_type_change(self, old_type: str, new_type: str) -> bool:
        """Check if a type change is breaking.

        Args:
            old_type: Previous type
            new_type: New type

        Returns:
            True if change may cause errors
        """
        old_lower = old_type.lower()
        new_lower = new_type.lower()

        # Check exact match first
        key = (old_lower, new_lower)
        if key in self.BREAKING_TYPE_CHANGES:
            return self.BREAKING_TYPE_CHANGES[key]

        # Numeric to string is generally safe
        if "int" in old_lower or "float" in old_lower:
            if "str" in new_lower:
                return False

        # String to numeric can be breaking
        if "str" in old_lower:
            if "int" in new_lower or "float" in new_lower:
                return True

        return False

    def load_schema_from_dataframe(self, df) -> list[SchemaColumn]:
        """Extract schema from a Polars DataFrame.

        Args:
            df: Polars DataFrame

        Returns:
            List of SchemaColumn
        """
        columns = []
        for col_name in df.columns:
            col = df[col_name]
            columns.append(
                SchemaColumn(
                    name=col_name,
                    dtype=str(col.dtype),
                    nullable=col.null_count() > 0,
                )
            )
        return columns

    def detect_evolution(
        self,
        baseline_path,
        current_path,
    ) -> SchemaEvolution:
        """Detect schema evolution between two data files.

        Args:
            baseline_path: Path to baseline data file
            current_path: Path to current data file

        Returns:
            SchemaEvolution with all changes
        """
        from mldata.core.normalize import NormalizeService

        normalize = NormalizeService()

        baseline_df = normalize.read_data(baseline_path)
        current_df = normalize.read_data(current_path)

        baseline_columns = self.load_schema_from_dataframe(baseline_df)
        current_columns = self.load_schema_from_dataframe(current_df)

        evolution = self.compare_schemas(baseline_columns, current_columns)
        evolution.baseline_path = str(baseline_path)
        evolution.current_path = str(current_path)

        return evolution
