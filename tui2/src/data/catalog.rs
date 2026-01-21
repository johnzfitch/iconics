use anyhow::{Context, Result};
use rusqlite::{Connection, Row};
use std::path::Path;

#[derive(Debug, Clone)]
pub struct Icon {
    pub id: String,
    pub filename: Option<String>,
    pub source_file: Option<String>,
    pub semantic_name: String,
    pub tags: Vec<String>,
    pub category: String,
    pub description: String,
    #[allow(dead_code)]
    pub used_in: Vec<String>,
    #[allow(dead_code)]
    pub metaphor: Option<String>,
    #[allow(dead_code)]
    pub emotional_valence: Option<f32>,
    #[allow(dead_code)]
    pub abstraction_level: Option<u8>,
}

impl Icon {
    /// Get the file path for this icon (filename or source_file)
    pub fn path(&self) -> Option<&str> {
        self.filename.as_deref().or(self.source_file.as_deref())
    }
}

#[derive(Debug)]
pub struct IconCatalog {
    #[allow(dead_code)]
    pub version: String,
    pub icons: Vec<Icon>,
}

impl IconCatalog {
    pub fn load_sqlite(db_path: &Path) -> Result<Self> {
        let conn = Connection::open(db_path).context("Failed to open SQLite catalog")?;

        let exists: bool = conn
            .query_row(
                "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'icons')",
                [],
                |row| row.get(0),
            )
            .context("Failed to query SQLite schema")?;
        if !exists {
            anyhow::bail!(
                "SQLite DB does not contain expected 'icons' table (did you run scripts/migrate_catalog_to_sqlite.py?)"
            );
        }

        let mut stmt = conn
            .prepare(
                r#"
                SELECT
                  i.id,
                  i.filename,
                  i.source_file,
                  i.semantic_name,
                  COALESCE((SELECT group_concat(t.tag, char(10)) FROM icon_tags t WHERE t.icon_id = i.id), '') AS tags_joined,
                  i.category,
                  i.description,
                  COALESCE((SELECT group_concat(u.used_in, char(10)) FROM icon_used_in u WHERE u.icon_id = i.id), '') AS used_in_joined,
                  i.metaphor,
                  i.emotional_valence,
                  i.abstraction_level
                FROM icons i
                ORDER BY i.semantic_name ASC
                "#,
            )
            .context("Failed to prepare SQLite query")?;

        let icons_iter = stmt
            .query_map([], |row| icon_from_row(row))
            .context("Failed to query icons")?;

        let mut icons = Vec::new();
        for icon in icons_iter {
            icons.push(icon?);
        }

        Ok(Self {
            version: "sqlite".to_string(),
            icons,
        })
    }
}

fn icon_from_row(row: &Row<'_>) -> rusqlite::Result<Icon> {
    let tags_joined: String = row.get("tags_joined")?;
    let used_in_joined: String = row.get("used_in_joined")?;

    let tags = split_joined_lines(&tags_joined);
    let used_in = split_joined_lines(&used_in_joined);

    let abstraction_level: Option<i64> = row.get("abstraction_level")?;

    Ok(Icon {
        id: row.get("id")?,
        filename: row.get("filename")?,
        source_file: row.get("source_file")?,
        semantic_name: row.get("semantic_name")?,
        tags,
        category: row.get("category")?,
        description: row.get("description")?,
        used_in,
        metaphor: row.get("metaphor")?,
        emotional_valence: row.get::<_, Option<f64>>("emotional_valence")?.map(|v| v as f32),
        abstraction_level: abstraction_level.map(|v| v as u8),
    })
}

fn split_joined_lines(value: &str) -> Vec<String> {
    value
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty())
        .map(|line| line.to_string())
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use rusqlite::Connection;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn temp_db_path() -> std::path::PathBuf {
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("time should be monotonic")
            .as_nanos();
        std::env::temp_dir().join(format!(
            "iconics-tui2-test-{}-{}.sqlite3",
            std::process::id(),
            nanos
        ))
    }

    #[test]
    fn loads_icons_from_sqlite_with_tags_and_used_in() {
        let db_path = temp_db_path();
        {
            let conn = Connection::open(&db_path).unwrap();
            conn.execute_batch(
                r#"
                PRAGMA foreign_keys = ON;
                CREATE TABLE icons (
                  id TEXT PRIMARY KEY,
                  semantic_name TEXT NOT NULL,
                  category TEXT NOT NULL,
                  description TEXT NOT NULL DEFAULT '',
                  filename TEXT,
                  source_file TEXT,
                  metaphor TEXT,
                  emotional_valence REAL,
                  abstraction_level INTEGER,
                  style TEXT,
                  enrichment_confidence REAL
                );
                CREATE TABLE icon_tags (
                  icon_id TEXT NOT NULL,
                  tag TEXT NOT NULL,
                  PRIMARY KEY (icon_id, tag),
                  FOREIGN KEY (icon_id) REFERENCES icons(id) ON DELETE CASCADE
                );
                CREATE TABLE icon_used_in (
                  icon_id TEXT NOT NULL,
                  used_in TEXT NOT NULL,
                  PRIMARY KEY (icon_id, used_in),
                  FOREIGN KEY (icon_id) REFERENCES icons(id) ON DELETE CASCADE
                );
                "#,
            )
            .unwrap();

            conn.execute(
                "INSERT INTO icons (id, semantic_name, category, description, filename) VALUES (?, ?, ?, ?, ?)",
                ("icon-1", "Icon One", "files", "Test icon", "raw/icon-1.png"),
            )
            .unwrap();
            conn.execute("INSERT INTO icon_tags (icon_id, tag) VALUES (?, ?)", ("icon-1", "tag-a"))
                .unwrap();
            conn.execute("INSERT INTO icon_tags (icon_id, tag) VALUES (?, ?)", ("icon-1", "tag-b"))
                .unwrap();
            conn.execute(
                "INSERT INTO icon_used_in (icon_id, used_in) VALUES (?, ?)",
                ("icon-1", "project-x"),
            )
            .unwrap();
        }

        let catalog = IconCatalog::load_sqlite(&db_path).unwrap();
        assert_eq!(catalog.icons.len(), 1);
        assert_eq!(catalog.icons[0].id, "icon-1");
        assert_eq!(catalog.icons[0].semantic_name, "Icon One");
        assert_eq!(catalog.icons[0].category, "files");
        assert_eq!(catalog.icons[0].tags.len(), 2);
        assert!(catalog.icons[0].tags.contains(&"tag-a".to_string()));
        assert!(catalog.icons[0].tags.contains(&"tag-b".to_string()));
        assert_eq!(catalog.icons[0].used_in, vec!["project-x".to_string()]);

        std::fs::remove_file(&db_path).ok();
    }
}
