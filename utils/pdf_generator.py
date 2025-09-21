# ==================== utils/pdf_generator.py ====================

from reportlab.lib.pagesizes import A4, A3, letter
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.http import HttpResponse
from datetime import datetime
import io


class ShelfLayoutPDFGenerator:
    """棚割りPDF生成クラス"""
    
    def __init__(self, proposal):
        self.proposal = proposal
        self.shelf = proposal.shelf
        self.pagesize = A4
        self.styles = getSampleStyleSheet()
        
        # カスタムスタイル
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=20,
            alignment=1  # 中央揃え
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12
        )
    
    def generate_comprehensive_pdf(self):
        """包括的な棚割りPDFを生成"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize, 
                               rightMargin=20*mm, leftMargin=20*mm,
                               topMargin=20*mm, bottomMargin=20*mm)
        
        story = []
        
        # 1. 表紙
        story.extend(self._create_cover_page())
        story.append(PageBreak())
        
        # 2. 提案概要
        story.extend(self._create_proposal_summary())
        story.append(Spacer(1, 20))
        
        # 3. 棚割りレイアウト図
        story.extend(self._create_layout_diagram())
        story.append(PageBreak())
        
        # 4. 商品配置一覧
        story.extend(self._create_product_list())
        story.append(PageBreak())
        
        # 5. 統計・分析
        story.extend(self._create_statistics())
        story.append(PageBreak())
        
        # 6. 推奨事項
        story.extend(self._create_recommendations())
        
        # PDF生成
        doc.build(story)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def _create_cover_page(self):
        """表紙ページ作成"""
        elements = []
        
        # タイトル
        title = Paragraph("棚割り提案書", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 30))
        
        # 提案情報テーブル
        proposal_data = [
            ['提案タイトル', self.proposal.title],
            ['得意先', self.proposal.customer.name],
            ['営業担当', self.proposal.sales_rep or '-'],
            ['提案日', self.proposal.proposal_date.strftime('%Y年%m月%d日')],
            ['棚名', self.shelf.name],
            ['棚サイズ', f'{self.shelf.width}×{self.shelf.height}×{self.shelf.depth}cm'],
            ['段数×列数', f'{self.shelf.rows}段×{self.shelf.columns}列'],
            ['作成日', datetime.now().strftime('%Y年%m月%d日 %H:%M')],
        ]
        
        proposal_table = Table(proposal_data, colWidths=[60*mm, 100*mm])
        proposal_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'HeiseiKakuGo-W5'),
            ('FONTNAME', (1, 0), (1, -1), 'HeiseiKakuGo-W5'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ]))
        
        elements.append(proposal_table)
        elements.append(Spacer(1, 40))
        
        # 概要説明
        if self.proposal.description:
            desc_title = Paragraph("提案概要", self.subtitle_style)
            elements.append(desc_title)
            description = Paragraph(self.proposal.description, self.styles['Normal'])
            elements.append(description)
        
        return elements
    
    def _create_proposal_summary(self):
        """提案概要作成"""
        elements = []
        
        title = Paragraph("配置統計サマリー", self.subtitle_style)
        elements.append(title)
        
        # 統計データ取得
        stats = self.proposal.get_placement_stats()
        
        # 統計テーブル
        stats_data = [
            ['項目', '数値', '比率'],
            ['総セル数', f"{stats['total_cells']}セル", '100%'],
            ['配置済みセル', f"{stats['occupied_cells']}セル", f"{stats['occupancy_rate']}%"],
            ['自社商品数', f"{stats['own_products_count']}商品", f"{stats['own_products_count']/max(1, stats['occupied_cells'])*100:.1f}%"],
            ['競合商品数', f"{stats['competitor_products_count']}商品", f"{stats['competitor_products_count']/max(1, stats['occupied_cells'])*100:.1f}%"],
            ['自社フェース数', f"{stats['own_faces']}フェース", f"{stats['own_share']}%"],
            ['競合フェース数', f"{stats['competitor_faces']}フェース", f"{100-stats['own_share']:.1f}%"],
        ]
        
        stats_table = Table(stats_data, colWidths=[60*mm, 50*mm, 40*mm])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'HeiseiKakuGo-W5'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ]))
        
        elements.append(stats_table)
        
        return elements
    
    def _create_layout_diagram(self):
        """レイアウト図作成"""
        elements = []
        
        title = Paragraph("棚割りレイアウト図", self.subtitle_style)
        elements.append(title)
        
        # 棚割り画像生成
        from shelves.models import ShelfPlacement
        placements = ShelfPlacement.objects.filter(shelf=self.shelf).select_related('product', 'product__maker')
        
        processor = ShelfImageProcessor(self.shelf)
        image_data = processor.generate_shelf_layout_image(placements, high_resolution=True)
        
        # 画像をPDFに追加
        image_buffer = io.BytesIO(image_data)
        img = RLImage(image_buffer, width=150*mm, height=100*mm)
        elements.append(img)
        
        return elements
    
    def _create_product_list(self):
        """商品配置一覧作成"""
        elements = []
        
        title = Paragraph("商品配置一覧", self.subtitle_style)
        elements.append(title)
        
        # 配置データ取得
        from shelves.models import ShelfPlacement
        placements = ShelfPlacement.objects.filter(shelf=self.shelf).select_related(
            'product', 'product__maker', 'product__brand', 'product__category'
        ).order_by('row', 'column')
        
        # テーブルデータ作成
        table_data = [
            ['位置', '商品名', 'JANコード', 'メーカー', 'カテゴリ', 'フェース数', '区分', 'サイズ']
        ]
        
        for placement in placements:
            position = f"{placement.row+1}段{placement.column+1}列"
            product_name = placement.product.product_name[:20] + ('...' if len(placement.product.product_name) > 20 else '')
            jan_code = placement.product.product_code
            maker = placement.product.maker.name[:15] + ('...' if len(placement.product.maker.name) > 15 else '')
            category = placement.product.category.name
            face_count = str(placement.face_count)
            product_type = '自社' if placement.product.is_own_product else '競合'
            size_info = f"{placement.span_rows}×{placement.span_columns}"
            
            table_data.append([
                position, product_name, jan_code, maker, category, face_count, product_type, size_info
            ])
        
        # テーブル作成
        product_table = Table(table_data, colWidths=[20*mm, 40*mm, 25*mm, 25*mm, 20*mm, 15*mm, 12*mm, 15*mm])
        product_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'HeiseiKakuGo-W5'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(product_table)
        
        return elements
    
    def _create_statistics(self):
        """統計・分析作成"""
        elements = []
        
        title = Paragraph("詳細分析", self.subtitle_style)
        elements.append(title)
        
        # サイズ分析
        from products.services import ProductSizeService
        size_analysis = ProductSizeService.analyze_size_distribution(self.shelf)
        
        # サイズ分布テーブル
        size_dist_data = [
            ['サイズカテゴリ', '商品数', '割合'],
            ['小型商品（1セル）', str(size_analysis['distribution']['small']), f"{size_analysis['distribution']['small']/max(1, size_analysis['total_products'])*100:.1f}%"],
            ['中型商品（2-4セル）', str(size_analysis['distribution']['medium']), f"{size_analysis['distribution']['medium']/max(1, size_analysis['total_products'])*100:.1f}%"],
            ['大型商品（5+セル）', str(size_analysis['distribution']['large']), f"{size_analysis['distribution']['large']/max(1, size_analysis['total_products'])*100:.1f}%"],
            ['サイズ未設定', str(size_analysis['distribution']['unknown']), f"{size_analysis['distribution']['unknown']/max(1, size_analysis['total_products'])*100:.1f}%"],
        ]
        
        size_table = Table(size_dist_data, colWidths=[60*mm, 40*mm, 30*mm])
        size_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'HeiseiKakuGo-W5'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ]))
        
        elements.append(size_table)
        
        return elements
    
    def _create_recommendations(self):
        """推奨事項作成"""
        elements = []
        
        title = Paragraph("改善推奨事項", self.subtitle_style)
        elements.append(title)
        
        # 推奨事項リスト
        recommendations = [
            "自社商品の目線レベル配置を増やし、視認性を向上させてください。",
            "大型商品は棚の端に配置し、安定性を確保してください。", 
            "同じブランドの商品をまとめて配置し、ブランド認知を向上させてください。",
            "フェース数を調整し、売上データに基づく最適配置を検討してください。",
            "競合商品との差別化を図るため、配置位置を戦略的に検討してください。"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            rec_text = Paragraph(f"{i}. {rec}", self.styles['Normal'])
            elements.append(rec_text)
            elements.append(Spacer(1, 8))
        
        return elements