TARGET := iphone:clang:latest:17.0
INSTALL_TARGET_PROCESSES = KalshiDashboard
ARCHS = arm64 arm64e

include $(THEOS)/makefiles/common.mk

APPLICATION_NAME = KalshiDashboard
KalshiDashboard_FILES = \
	../KalshiDashboard/App/KalshiDashboardApp.swift \
	../KalshiDashboard/ContentView.swift \
	../KalshiDashboard/Models/BotState.swift \
	../KalshiDashboard/ViewModels/DashboardViewModel.swift \
	../KalshiDashboard/Views/OverviewView.swift \
	../KalshiDashboard/Views/PositionsView.swift \
	../KalshiDashboard/Views/AnalyticsView.swift \
	../KalshiDashboard/Views/Components/GlassCard.swift \
	../KalshiDashboard/Views/Components/SparklineView.swift \
	../KalshiDashboard/Theme/AppTheme.swift
KalshiDashboard_FRAMEWORKS = SwiftUI UIKit Foundation Charts
KalshiDashboard_CODESIGN_FLAGS = -Sentitlements.plist

include $(THEOS_MAKE_PATH)/application.mk
