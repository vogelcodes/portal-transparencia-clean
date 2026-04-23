"""Flatten ARP / ArpItem / ArpEmpenho rows into a portable bundle dict."""
from datetime import datetime, timezone


def flatten_uasg(user_uasg_id):
    from src.auth.models import UserUasg, Arp, ArpItem

    u = UserUasg.query.get(user_uasg_id)
    if not u:
        raise ValueError(f"UserUasg {user_uasg_id} not found")

    arps = (Arp.query.filter_by(user_uasg_id=u.id)
            .order_by(Arp.data_vigencia_inicial.desc().nullslast())
            .all())

    meta_arps = []
    meta_itens = []
    meta_saldos = []

    for arp in arps:
        arp_row = {
            'numero_ata': arp.numero_ata_registro_preco or '',
            'numero_controle': arp.numero_controle_pncp_ata or '',
            'vigencia_inicial': arp.data_vigencia_inicial.strftime('%d/%m/%Y') if arp.data_vigencia_inicial else '',
            'vigencia_final': arp.data_vigencia_final.strftime('%d/%m/%Y') if arp.data_vigencia_final else '',
            'objeto': arp.objeto or '',
        }

        item_count = 0
        saldo_count = 0

        for item in arp.items.order_by(ArpItem.numero_item).all():
            rj = item.raw_json or {}
            emps = item.empenhos.all()

            qtd_empenhada_total = sum(
                float((e.raw_json or {}).get('quantidadeEmpenhada') or 0)
                for e in emps
            )
            qtd_hom = float(rj.get('quantidadeHomologadaItem') or 0)
            pct = round(qtd_empenhada_total / qtd_hom * 100, 1) if qtd_hom else None

            meta_itens.append({
                'numero_ata': arp.numero_ata_registro_preco or '',
                'numero_item': item.numero_item,
                'descricao': item.descricao or rj.get('descricaoItem') or '',
                'fornecedor_ni': rj.get('niFornecedor') or '',
                'fornecedor_nome': rj.get('nomeRazaoSocialFornecedor') or '',
                'valor_unitario': float(rj.get('valorUnitario') or item.valor_unitario or 0) or None,
                'valor_total': float(rj.get('valorTotal') or 0) or None,
                'qtd_registrada': float(rj.get('quantidadeRegistrada') or item.quantidade or 0) or None,
                'qtd_homologada': qtd_hom or None,
                'qtd_empenhada_total': qtd_empenhada_total or None,
                'pct_empenhado': pct,
                'total_saldos': len(emps),
            })
            item_count += 1

            for e in emps:
                ej = e.raw_json or {}
                upd = ej.get('dataHoraAtualizacao') or ''
                inc = ej.get('dataHoraInclusao') or ''
                meta_saldos.append({
                    'numero_ata': arp.numero_ata_registro_preco or '',
                    'numero_item': item.numero_item,
                    'descricao_item': item.descricao or rj.get('descricaoItem') or '',
                    'unidade': ej.get('unidade') or '',
                    'tipo': ej.get('tipo') or '',
                    'qtd_registrada': ej.get('quantidadeRegistrada'),
                    'qtd_empenhada': ej.get('quantidadeEmpenhada'),
                    'saldo_empenho': ej.get('saldoEmpenho'),
                    'data_inclusao': inc[:16].replace('T', ' ') if inc else '',
                    'data_atualizacao': upd[:16].replace('T', ' ') if upd else '',
                })
                saldo_count += 1

        arp_row['total_itens'] = item_count
        arp_row['total_saldos'] = saldo_count
        meta_arps.append(arp_row)

    return {
        'meta': {
            'codigo_uasg': u.codigo_uasg,
            'nome_uasg': u.nome_uasg or u.codigo_uasg,
            'sigla_uf': u.sigla_uf or '',
            'municipio': u.nome_municipio or '',
            'cnpj': u.cnpj or '',
            'generated_at': datetime.now(timezone.utc).astimezone().strftime('%d/%m/%Y %H:%M:%S'),
            'total_arps': len(meta_arps),
            'total_itens': len(meta_itens),
            'total_saldos': len(meta_saldos),
        },
        'arps': meta_arps,
        'itens': meta_itens,
        'saldos': meta_saldos,
    }
