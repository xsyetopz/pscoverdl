/*
⣞⢽⢪⢣⢣⢣⢫⡺⡵⣝⡮⣗⢷⢽⢽⢽⣮⡷⡽⣜⣜⢮⢺⣜⢷⢽⢝⡽⣝
⠸⡸⠜⠕⠕⠁⢁⢇⢏⢽⢺⣪⡳⡝⣎⣏⢯⢞⡿⣟⣷⣳⢯⡷⣽⢽⢯⣳⣫⠇
⠀⠀⢀⢀⢄⢬⢪⡪⡎⣆⡈⠚⠜⠕⠇⠗⠝⢕⢯⢫⣞⣯⣿⣻⡽⣏⢗⣗⠏⠀
⠀⠪⡪⡪⣪⢪⢺⢸⢢⢓⢆⢤⢀⠀⠀⠀⠀⠈⢊⢞⡾⣿⡯⣏⢮⠷⠁⠀⠀
⠀⠀⠀⠈⠊⠆⡃⠕⢕⢇⢇⢇⢇⢇⢏⢎⢎⢆⢄⠀⢑⣽⣿⢝⠲⠉⠀⠀⠀⠀
⠀⠀⠀⠀⠀⡿⠂⠠⠀⡇⢇⠕⢈⣀⠀⠁⠡⠣⡣⡫⣂⣿⠯⢪⠰⠂⠀⠀⠀⠀
⠀⠀⠀⠀⡦⡙⡂⢀⢤⢣⠣⡈⣾⡃⠠⠄⠀⡄⢱⣌⣶⢏⢊⠂⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢝⡲⣜⡮⡏⢎⢌⢂⠙⠢⠐⢀⢘⢵⣽⣿⡿⠁⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠨⣺⡺⡕⡕⡱⡑⡆⡕⡅⡕⡜⡼⢽⡻⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣳⣫⣾⣵⣗⡵⡱⡡⢣⢑⢕⢜⢕⡝⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⣿⣾⣿⣿⣿⡿⡽⡑⢌⠪⡢⡣⣣⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡟⡾⣿⢿⢿⢵⣽⣾⣼⣘⢸⢸⣞⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠁⠇⠡⠩⡫⢿⣝⡻⡮⣒⢽⠋⠀⠀⠀

    NO COVERS?
*/

package gui

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"

	wailsRuntime "github.com/wailsapp/wails/v2/pkg/runtime"
)

// CurrentVersion is the GUI version displayed in the window title and update check.
const CurrentVersion = "1.1"

// Config contains CLI options collected by the GUI.
type Config struct {
	CLIPath      string `json:"cliPath"`
	Emulator     string `json:"emulator"`
	CoverDir     string `json:"coverDir"`
	GameListPath string `json:"gameListPath"`
	CoverType    string `json:"coverType"`
	Fallback     bool   `json:"fallback"`
	UseHTTP      bool   `json:"useHTTP"`
	Workers      int    `json:"workers"`
}

// EmulatorConfig stores persisted form values for one emulator tab.
type EmulatorConfig struct {
	CoverDirectory string `json:"coverDirectory"`
	GameCache      string `json:"gameCache"`
	CoverType      int    `json:"coverType"`
	UseSSL         bool   `json:"useSSL"`
	Fallback       bool   `json:"fallback"`
}

// StoredConfig stores persisted GUI settings for both emulator tabs.
type StoredConfig struct {
	DuckStation EmulatorConfig `json:"duckstation"`
	PCSX2       EmulatorConfig `json:"pcsx2"`
}

// DownloadResult is returned to the Wails frontend after invoking the CLI.
type DownloadResult struct {
	Command string `json:"command"`
	Output  string `json:"output"`
	Error   string `json:"error"`
}

// UpdateStatus describes the remote version check result.
type UpdateStatus struct {
	Version             string `json:"version"`
	LatestVersion       string `json:"latestVersion"`
	NewVersionAvailable bool   `json:"newVersionAvailable"`
}

// App exposes Wails-bound GUI methods.
type App struct {
	ctx     context.Context
	cliPath string
}

var commandContext = exec.CommandContext

// NewApp creates a Wails GUI backend.
func NewApp(cliPath string) *App {
	return &App{cliPath: cliPath}
}

// Startup stores the Wails context for dialogs and cancellation.
func (a *App) Startup(ctx context.Context) {
	a.ctx = ctx
}

// BuildCLIArgs converts GUI config into pscoverdl CLI arguments.
func BuildCLIArgs(cfg Config) ([]string, error) {
	cfg.Emulator = strings.ToLower(strings.TrimSpace(cfg.Emulator))
	cfg.CoverType = strings.ToLower(strings.TrimSpace(cfg.CoverType))
	if cfg.CoverType == "" {
		cfg.CoverType = "default"
	}
	if cfg.Workers <= 0 {
		cfg.Workers = 4
	}
	if cfg.Emulator != "pcsx2" && cfg.Emulator != "duckstation" {
		return nil, errors.New("emulator must be pcsx2 or duckstation")
	}
	if strings.TrimSpace(cfg.CoverDir) == "" {
		return nil, errors.New("cover directory is required")
	}
	if strings.TrimSpace(cfg.GameListPath) == "" {
		return nil, errors.New("game cache is required")
	}
	if cfg.CoverType != "default" && cfg.CoverType != "3d" {
		return nil, errors.New("cover type must be default or 3d")
	}

	args := []string{
		"-emulator", cfg.Emulator,
		"-covers", cfg.CoverDir,
		"-gamelist", cfg.GameListPath,
		"-type", cfg.CoverType,
		"-workers", strconv.Itoa(cfg.Workers),
	}
	if cfg.Fallback {
		args = append(args, "-fallback")
	}
	if cfg.UseHTTP {
		args = append(args, "-http")
	}
	return args, nil
}

// DefaultCLIPath returns the CLI binary path expected next to the GUI binary.
func DefaultCLIPath() string {
	exe, err := os.Executable()
	if err != nil {
		return executableName()
	}
	return filepath.Join(filepath.Dir(exe), executableName())
}

// ConfigPath returns the platform-specific GUI configuration path.
func ConfigPath() (string, error) {
	var base string
	switch runtime.GOOS {
	case "windows":
		base = os.Getenv("APPDATA")
		if base == "" {
			base = homeDir()
		}
	case "darwin":
		base = filepath.Join(homeDir(), "Library", "Application Support")
	default:
		base = os.Getenv("XDG_CONFIG_HOME")
		if base == "" {
			base = filepath.Join(homeDir(), ".config")
		}
	}
	if base == "" {
		return "", errors.New("cannot determine config directory")
	}
	dir := filepath.Join(base, "pscoverdl")
	//nolint:gosec // APPDATA/XDG_CONFIG_HOME are platform-defined user config roots.
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return "", err
	}
	return filepath.Join(dir, "pscoverdl.json"), nil
}

// LoadConfig loads persisted GUI settings for the frontend.
func (a *App) LoadConfig() StoredConfig {
	return LoadConfigFile()
}

// LoadConfigFile loads persisted GUI settings from disk.
func LoadConfigFile() StoredConfig {
	cfg := defaultStoredConfig()
	path, err := ConfigPath()
	if err != nil {
		return cfg
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return cfg
	}
	_ = json.Unmarshal(data, &cfg)
	return cfg
}

// SaveConfig persists GUI settings from the frontend.
func (a *App) SaveConfig(cfg StoredConfig) string {
	if err := SaveConfigFile(cfg); err != nil {
		return err.Error()
	}
	return ""
}

// SaveConfigFile writes GUI settings to disk.
func SaveConfigFile(cfg StoredConfig) error {
	path, err := ConfigPath()
	if err != nil {
		return err
	}
	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o600)
}

// SelectCoverDirectory opens a native directory picker.
func (a *App) SelectCoverDirectory() string {
	if a.ctx == nil {
		return ""
	}
	path, err := wailsRuntime.OpenDirectoryDialog(a.ctx, wailsRuntime.OpenDialogOptions{Title: "Select cover directory"})
	if err != nil {
		return ""
	}
	return path
}

// SelectGameCache opens a native gamelist.cache picker.
func (a *App) SelectGameCache() string {
	if a.ctx == nil {
		return ""
	}
	path, err := wailsRuntime.OpenFileDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title:   "Select gamelist.cache",
		Filters: []wailsRuntime.FileFilter{{DisplayName: "Game cache (*.cache)", Pattern: "*.cache"}},
	})
	if err != nil {
		return ""
	}
	return path
}

// StartDownload invokes the CLI with options selected in the GUI.
func (a *App) StartDownload(cfg Config) DownloadResult {
	args, err := BuildCLIArgs(cfg)
	if err != nil {
		return DownloadResult{Error: err.Error()}
	}
	cliPath := strings.TrimSpace(cfg.CLIPath)
	if cliPath == "" {
		cliPath = strings.TrimSpace(a.cliPath)
	}
	if cliPath == "" {
		cliPath = DefaultCLIPath()
	}

	ctx := context.Background()
	if a.ctx != nil {
		ctx = a.ctx
	}
	cmd := commandContext(ctx, cliPath, args...)
	var output bytes.Buffer
	cmd.Stdout = &output
	cmd.Stderr = &output
	err = cmd.Run()
	result := DownloadResult{Command: cliPath + " " + strings.Join(args, " "), Output: output.String()}
	if err != nil {
		result.Error = err.Error()
	}
	return result
}

// CheckUpdates checks GitHub for a newer version.
func (a *App) CheckUpdates() UpdateStatus {
	status := UpdateStatus{Version: CurrentVersion, LatestVersion: CurrentVersion}
	client := http.Client{Timeout: 5 * time.Second}
	req, err := http.NewRequestWithContext(context.Background(), http.MethodGet, "https://github.com/xlenore/pscoverdl/raw/main/VERSION", nil)
	if err != nil {
		return status
	}
	resp, err := client.Do(req)
	if err != nil {
		return status
	}
	defer resp.Body.Close()
	buf := make([]byte, 32)
	n, _ := resp.Body.Read(buf)
	latest := strings.TrimSpace(string(buf[:n]))
	if latest != "" {
		status.LatestVersion = latest
		status.NewVersionAvailable = latest != CurrentVersion
	}
	return status
}

func defaultStoredConfig() StoredConfig {
	return StoredConfig{
		DuckStation: EmulatorConfig{CoverType: 0, UseSSL: true},
		PCSX2:       EmulatorConfig{CoverType: 0, UseSSL: true},
	}
}

func homeDir() string {
	home, _ := os.UserHomeDir()
	return home
}

func executableName() string {
	if runtime.GOOS == "windows" {
		return "pscoverdl.exe"
	}
	return "pscoverdl"
}

// CoverTypeString converts the legacy GUI cover type integer to a CLI value.
func CoverTypeString(value int) string {
	if value == 1 {
		return "3d"
	}
	return "default"
}

// ConfigForEmulator converts persisted emulator settings to CLI config.
func ConfigForEmulator(emulator string, cfg EmulatorConfig) Config {
	return Config{
		Emulator:     emulator,
		CoverDir:     cfg.CoverDirectory,
		GameListPath: cfg.GameCache,
		CoverType:    CoverTypeString(cfg.CoverType),
		UseHTTP:      !cfg.UseSSL,
		Fallback:     cfg.Fallback,
		Workers:      4,
	}
}

func (r DownloadResult) String() string {
	if r.Error != "" {
		return fmt.Sprintf("%s\n%s", r.Error, r.Output)
	}
	return r.Output
}
