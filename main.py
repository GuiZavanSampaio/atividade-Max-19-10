
from ofxparse import OfxParser
from decimal import Decimal
from config import DB_CONFIG
import psycopg2

# 1. Ler o arquivo OFX
with open("extrato.ofx", "rb") as arquivo:
    ofx = OfxParser.parse(arquivo)

transacoes = ofx.account.statement.transactions

entradas = Decimal("0.00")
saidas = Decimal("0.00")

print("\n========== EXTRATO BANCÁRIO ==========\n")

# 2. Exibir movimentações e calcular os totais
for t in transacoes:
    valor = Decimal(str(t.amount))
    descricao = (t.memo or "Sem descrição")[:255]

    print(f"Data      : {t.date.strftime('%d/%m/%Y')}")
    print(f"Valor     : R$ {valor:.2f}")
    print(f"Descrição : {descricao}")
    print("-" * 40)

    if valor > 0:
        entradas += valor
    elif valor < 0:
        saidas += valor

saldo = entradas + saidas

print("\n========== RESUMO FINANCEIRO ==========")
print(f"Quantidade de movimentações: {len(transacoes)}")
print(f"Total de entradas: R$ {entradas:.2f}")
print(f"Total de saídas: R$ {saidas:.2f}")
print(f"Saldo calculado: R$ {saldo:.2f}")

# 3. Conectar ao PostgreSQL e salvar as movimentações
try:
    print("\nConectando ao PostgreSQL...")

    with psycopg2.connect(**DB_CONFIG) as conexao:
        with conexao.cursor() as cursor:

            inseridas = 0
            duplicadas = 0

            for t in transacoes:
                data = t.date.date()
                valor = Decimal(str(t.amount))
                descricao = (t.memo or "Sem descrição")[:255]
                fitid = str(t.id).strip() if t.id else None

                if fitid:
                    cursor.execute(
                        """
                        INSERT INTO public.movimentacoes
                            (data_movimentacao, valor, descricao, fitid)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (fitid) DO NOTHING
                        RETURNING id;
                        """,
                        (data, valor, descricao, fitid)
                    )
                else:
                    # Evita repetir transações sem FITID.
                    cursor.execute(
                        """
                        INSERT INTO public.movimentacoes
                            (data_movimentacao, valor, descricao)
                        SELECT %s, %s, %s
                        WHERE NOT EXISTS (
                            SELECT 1
                            FROM public.movimentacoes
                            WHERE data_movimentacao = %s
                              AND valor = %s
                              AND descricao = %s
                        )
                        RETURNING id;
                        """,
                        (data, valor, descricao, data, valor, descricao)
                    )

                if cursor.fetchone():
                    inseridas += 1
                else:
                    duplicadas += 1

    print("\n========== POSTGRESQL ==========")
    print(f"Movimentações inseridas: {inseridas}")
    print(f"Duplicadas ignoradas: {duplicadas}")
    print("Importação concluída com sucesso!")

except Exception as erro:
    print("\nErro ao salvar no PostgreSQL:")
    print(erro)
